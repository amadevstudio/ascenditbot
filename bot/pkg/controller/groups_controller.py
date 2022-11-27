from aiogram import types

from lib.language import localization
from framework.controller.message_tools import message_sender, go_back_inline_markup, call_or_command
from pkg.service import user_storage


async def add_group(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    if call_or_command(call, message):
        message_structures = [{
            'type': 'image',
            'image': types.InputFile(f"./public/anonim_admin_example_ru.jpg"),
            'text': localization.get_message(["add_group", "instruction"], message.from_user.language_code),
            'reply_markup': go_back_inline_markup(message.from_user.language_code)
        }]
        await message_sender(message, resending=call is None, message_structures=message_structures)

        if change_user_state:
            user_storage.change_page(message.chat.id, 'add_group')

        return

    # Group adding

    print("!")
    print(message.forward_from)
    print(message.forward_from_chat)
    print(message.forward_from_chat.id)
    # {"id": -1001810942288, "title": "message_manager_bot_test", "type": "supergroup"}
    # -1001810942288

    # if message.forward_from is not None \
    #         and hasattr(message.forward_from, "channel_id") \
    #         and message.forward_from.channel_id != 0:
    #
    #     channel_id = message.fwd_from.channel_id
    # else:
    #     channel_id = message.text
    # result = service.group.add_group()
