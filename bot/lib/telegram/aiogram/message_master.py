import enum
import json
import re
from typing import *
from urllib.parse import unquote

import aiogram
from aiogram import types
from aiogram.utils import keyboard


def get_timeout_from_error_bot(error):
    result = re.search(r'Too Many Requests: retry after ([0-9]+)', str(error))
    if result is not None:
        try:
            return int(result[1]) + 1
        except Exception:
            pass
    return False


class MasterMessages(enum.Enum):
    text = 'text'
    image = 'image'

    @staticmethod
    def all_types():
        return [x.value for x in list(MasterMessages)]


LOADING_TYPE = MasterMessages.text.value


class ButtonData(TypedDict):
    text: str
    callback_data: str | dict[str, Any]


message_types = Literal['text', 'image']


class MessageStructuresInterface(TypedDict, total=False):
    type: message_types
    text: str
    reply_markup: list[list[ButtonData]]
    parse_mode: Literal['MarkdownV2', 'HTML'] | None
    disable_web_page_preview: bool
    image: str | types.InputFile


class PreviousMessageStructuresInterface(TypedDict):
    id: int
    type: message_types


def build_new_prev_message_structure(message_id: int,
                                     message_type: message_types) -> PreviousMessageStructuresInterface:
    result = {
        'id': message_id,
        'type': message_type
    }

    return result


def build_markup(markup: list[list[ButtonData]] | None):
    if markup is None:
        return None

    keyboard_builder = keyboard.InlineKeyboardBuilder()
    for row in markup:
        row_buttons = []
        for button_data in row:
            if isinstance(button_data['callback_data'], str):
                callback_data = button_data['callback_data']
            elif isinstance(button_data['callback_data'], dict):
                callback_data = json.dumps(button_data['callback_data'])
            else:
                callback_data = None

            row_buttons.append(keyboard.InlineKeyboardButton(
                text=button_data.get('text', ''),
                callback_data=callback_data))

        keyboard_builder.row(*row_buttons)
    return keyboard_builder.as_markup()


# resending: позволяет принудительно отправить сообщение повторно
# postloading: обработка случаев, когда до это отправляется сообщение "загрузка"
async def message_master(
        bot: aiogram.Bot, aiogram_message: types.Message,
        resending=False,
        message_structures=None,
        previous_message_structures=None
) -> List[PreviousMessageStructuresInterface]:
    if message_structures is None:
        message_structures = []
    if previous_message_structures is None:
        previous_message_structures = []

    for message_structure in message_structures:
        # Unquote url
        if 'image' in message_structure and isinstance(message_structure['image'], str):
            message_structure['image'] = unquote(message_structure['image'])

    def message_structure_filter(filtrating_message_structure):
        return filtrating_message_structure['type'] in MasterMessages.all_types()

    message_structures = list(filter(message_structure_filter, message_structures))

    # Mark old messages as delete, new as send and old-to-new as edit
    messages_to_delete = []  # old messages
    messages_to_edit = {}  # old message id => new message structure
    messages_to_send = []  # new messages

    if resending:
        previous_message_structures = []

    # Constructing
    i = 0
    message_structures_len = len(message_structures)
    for previous_message_structure in previous_message_structures:
        if i >= message_structures_len:
            messages_to_delete.append(previous_message_structure)
            continue

        message_structure = message_structures[i]
        if previous_message_structure['type'] != message_structure['type']:
            messages_to_delete.append(previous_message_structure)
        else:
            messages_to_edit[previous_message_structure['id']] = message_structure
            i += 1

    for j in range(i, message_structures_len):
        messages_to_send.append(message_structures[j])

    # Array to return
    new_message_structures = []

    for message_to_delete in messages_to_delete:
        try:
            await bot.delete_message(aiogram_message.chat.id, message_to_delete['id'])
        except Exception:
            messages_to_send = message_structures
            messages_to_edit = []
            break

    result: types.Message | None

    for message_to_edit_id in messages_to_edit:
        message_structure = messages_to_edit[message_to_edit_id]

        reply_markup = build_markup(message_structure.get('reply_markup', None))

        if message_structure['type'] == MasterMessages.text.value:
            result = await bot.edit_message_text(
                text=message_structure.get('text', None),
                chat_id=aiogram_message.chat.id,
                message_id=message_to_edit_id,
                parse_mode=message_structure.get('parse_mode', None),
                reply_markup=reply_markup,
                disable_web_page_preview=message_structure.get('disable_web_page_preview', None))

        elif message_structure['type'] == MasterMessages.image.value:
            result = await bot.edit_message_media(
                media=message_structure.get('image', None),
                chat_id=aiogram_message.chat.id,
                message_id=message_to_edit_id)
            await bot.edit_message_caption(
                chat_id=aiogram_message.chat.id,
                message_id=message_to_edit_id,
                caption=message_structure.get('text', None),
                parse_mode=message_structure.get('parse_mode', None),
                reply_markup=reply_markup)

        else:
            result = None

        if result is not None:
            new_message_structures.append(
                build_new_prev_message_structure(result.message_id, message_structure['type']))

    for message_to_send in messages_to_send:
        message_structure = message_to_send

        reply_markup = build_markup(message_structure.get('reply_markup', None))

        if message_structure['type'] == MasterMessages.text.value:
            result = await aiogram_message.answer(
                text=message_structure.get('text', None),
                parse_mode=message_structure.get('parse_mode', None),
                reply_markup=reply_markup,
                disable_web_page_preview=message_structure.get('disable_web_page_preview', None))

        elif message_structure['type'] == MasterMessages.image.value:
            result = await aiogram_message.answer_photo(
                photo=message_structure.get('image', None),
                caption=message_structure.get('text', None),
                parse_mode=message_structure.get('parse_mode', None),
                reply_markup=reply_markup)

        else:
            result = None

        if result is not None:
            new_message_structures.append(
                build_new_prev_message_structure(result.message_id, message_structure['type']))

    return new_message_structures
