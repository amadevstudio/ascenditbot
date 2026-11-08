"""Admin, Channels: the channels whose subscribers get the bonus days (pkg/service/channel_bonus.py); one is added
by sending its @username, a t.me link or the id, the bot being an admin there."""
import html
import re

from aiogram.exceptions import TelegramAPIError

from framework.controller.message_tools import go_back_inline_markup, is_call_or_command, message_sender, notify
from framework.controller.types import ControllerParams
from framework.system.bot_setup import bot
from pkg.repository import channel_bonus_repository
from pkg.service.channel_bonus import BONUS_DAYS, ChannelBonus
from pkg.system.logger import logger


async def page(params: ControllerParams):
    channels = await ChannelBonus.channels()
    lines = [f"<b>Каналы за подписку</b> (+{BONUS_DAYS} дней платного тарифа)", ""]
    if not channels:
        lines.append("Пока ни одного: бонус в меню не показывается.")
    for number, channel in enumerate(channels, 1):
        name = html.escape(channel['title'] or channel['service_id'])
        link = f"<a href=\"{html.escape(channel['link'])}\">{name}</a>" if channel['link'] else name
        lines.append(f"{number}. {link}: взяли бонус {channel['claimed']}, из них отписались {channel['lost']}")
    buttons = [[{'text': f"🗑 {channel['title'] or channel['service_id']}",
                 'callback_data': {'tp': 'admin_delete_channel', 'id': channel['id']}}] for channel in channels]
    buttons += [[{'text': "➕ Добавить канал", 'callback_data': {'tp': 'admin_add_channel'}}],
                *go_back_inline_markup(params['language_code'])]
    await message_sender(params['message'].chat.id, message_structures=[{
        'type': 'text', 'text': "\n".join(lines), 'parse_mode': 'HTML', 'disable_web_page_preview': True,
        'reply_markup': buttons}])


async def delete_channel(params: ControllerParams):
    removed = await channel_bonus_repository.delete_channel(int(params['state_data']['id']))
    await notify(params['call'], params['message'], f"Убран: {removed['title']}" if removed else "Уже убран")
    await page(params)


def _chat_ref(text: str) -> str | int | None:
    text = text.strip()
    if re.fullmatch(r'-?\d+', text):
        return int(text)
    match = re.fullmatch(r'(?:https?://)?(?:t\.me/|@)?([A-Za-z][A-Za-z0-9_]{3,31})/?', text)
    return '@' + match.group(1) if match else None


async def add_channel(params: ControllerParams):
    """"➕ Добавить канал": the bot waits for the channel and checks it can see who is subscribed there."""
    call, message, language_code = params['call'], params['message'], params['language_code']
    if is_call_or_command(call, message):
        await message_sender(message.chat.id, message_structures=[{
            'type': 'text',
            'text': "Пришлите @username канала, ссылку t.me или id. Бот должен быть админом канала: иначе "
                    "Telegram не скажет ему, кто подписан.",
            'reply_markup': go_back_inline_markup(language_code)}])
        return

    ref = _chat_ref(message.text or '')
    if ref is None:
        await notify(None, message, "Не похоже на канал: пришлите @username, ссылку t.me или id.", save_state=True)
        return
    try:
        chat = await bot.get_chat(ref)
        # The check the bonus relies on: can the bot see who is subscribed?
        await bot.get_chat_member(chat.id, message.chat.id)
    except TelegramAPIError as e:
        logger.warning('Cannot add a bonus channel', ref, e)
        await notify(None, message, "Не получается проверить подписчиков этого канала. Сделайте бота админом "
                                    f"канала и пришлите ещё раз.\n\nTelegram: {e}", save_state=True)
        return
    link = ChannelBonus.link(chat)
    if not link:
        await notify(None, message, "У канала нет ни @username, ни ссылки-приглашения: людям некуда перейти. "
                                    "Сделайте канал публичным или создайте ссылку и пришлите ещё раз.",
                     save_state=True)
        return
    await channel_bonus_repository.add_channel(str(chat.id), chat.title, link)
    await message_sender(message.chat.id, message_structures=[{
        'type': 'text', 'parse_mode': 'HTML',
        'text': f"✅ Канал <b>{html.escape(chat.title or str(chat.id))}</b> добавлен.\n\n"
                "Пришлите ещё один или вернитесь назад.",
        'reply_markup': go_back_inline_markup(language_code)}])
