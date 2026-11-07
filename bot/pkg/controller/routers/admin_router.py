"""/admin for the bot's owner (users.is_admin): the channels whose subscribers get the bonus days
(pkg/service/channel_bonus.py). /addchannel @name adds one, the buttons remove. Others get nothing here.
Joins and leaves in those channels (chat_member, sent to the channel's admins) check the bonus at once."""
import html
import json
import re

from aiogram import F, Router
from aiogram.filters import BaseFilter, Command, CommandObject
from aiogram.types import CallbackQuery, ChatMemberUpdated, InlineKeyboardButton, InlineKeyboardMarkup, Message

from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from pkg.repository import channel_bonus_repository
from pkg.service.channel_bonus import BONUS_DAYS, ChannelBonus
from pkg.service.user import User
from pkg.system.logger import logger


class BotOwner(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = await User.find_by_service_id(event.from_user.id) if event.from_user else None
        return user is not None and bool(user['is_admin'])


class RemoveChannel(BaseFilter):
    async def __call__(self, call: CallbackQuery) -> dict | bool:
        try:
            data = json.loads(call.data or '')
        except ValueError:
            return False
        if not isinstance(data, dict) or data.get('tp') != 'adm_ch_del':
            return False
        return {'channel_id': int(data['id'])}


async def channels_page() -> tuple[str, InlineKeyboardMarkup]:
    channels = await channel_bonus_repository.channels()
    lines = [f"<b>Каналы за подписку</b> (+{BONUS_DAYS} дней платного тарифа)", ""]
    if not channels:
        lines.append("Пока ни одного: бонус в меню не показывается.")
    for number, channel in enumerate(channels, 1):
        name = html.escape(channel['title'] or channel['service_id'])
        link = f"<a href=\"{html.escape(channel['link'])}\">{name}</a>" if channel['link'] else name
        lines.append(f"{number}. {link}: взяли бонус {channel['claimed']}, из них отписались {channel['lost']}")
    lines += ["", "Добавить: <code>/addchannel @username</code> (или ссылка t.me, или id). Бот должен быть "
                  "админом канала: иначе Telegram не скажет ему, кто подписан."]
    buttons = [[InlineKeyboardButton(text=f"🗑 {channel['title'] or channel['service_id']}", callback_data=json.dumps(
        {'tp': 'adm_ch_del', 'id': channel['id']}, separators=(',', ':')))] for channel in channels]
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=buttons)


def _chat_ref(text: str) -> str | int | None:
    text = text.strip()
    if re.fullmatch(r'-?\d+', text):
        return int(text)
    match = re.fullmatch(r'(?:https?://)?(?:t\.me/|@)?([A-Za-z][A-Za-z0-9_]{3,31})/?', text)
    return '@' + match.group(1) if match else None


def admin_router() -> Router:
    router = Router()
    router.message.filter(F.chat.type == 'private')

    @router.message(Command('admin'), BotOwner())
    async def admin(message: Message):
        text, markup = await channels_page()
        await message.answer(text, parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)

    @router.message(Command('addchannel'), BotOwner())
    async def add_channel(message: Message, command: CommandObject):
        ref = _chat_ref(command.args or '')
        if ref is None:
            await message.answer("Пришлите так: <code>/addchannel @username</code>", parse_mode='HTML')
            return
        try:
            chat = await message.bot.get_chat(ref)
            # The check the bonus relies on: can the bot see who is subscribed?
            await message.bot.get_chat_member(chat.id, message.from_user.id)
        except TelegramAPIError as e:
            logger.warning('Cannot add a bonus channel', ref, e)
            await message.answer("Не получается проверить подписчиков этого канала. Сделайте бота админом канала "
                                 f"и попробуйте ещё раз.\n\nTelegram: {html.escape(str(e))}", parse_mode='HTML')
            return
        link = f"https://t.me/{chat.username}" if chat.username else chat.invite_link
        if not link:
            await message.answer("У канала нет ни @username, ни ссылки-приглашения: людям некуда перейти. "
                                 "Сделайте канал публичным или создайте ссылку и попробуйте ещё раз.")
            return
        await channel_bonus_repository.add_channel(str(chat.id), chat.title, link)
        text, markup = await channels_page()
        await message.answer(text, parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)

    @router.callback_query(RemoveChannel(), BotOwner())
    async def remove_channel(call: CallbackQuery, channel_id: int):
        removed = await channel_bonus_repository.delete_channel(channel_id)
        await call.answer(f"Убран: {removed['title']}" if removed else "Уже убран")
        text, markup = await channels_page()
        try:
            await call.message.edit_text(text, parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)
        except TelegramBadRequest as e:
            if 'message is not modified' not in str(e):
                logger.warning('Cannot edit the admin page', e)

    @router.chat_member(F.chat.type == 'channel')
    async def channel_membership(event: ChatMemberUpdated):
        """Left or joined a bonus channel: no waiting for the daily check."""
        from pkg.background.async_tasks.subscription_handler import notify_bonus_lost
        was, now = ChannelBonus.in_channel(event.old_chat_member), ChannelBonus.in_channel(event.new_chat_member)
        if was == now:
            return
        try:
            await ChannelBonus.membership_changed(
                str(event.chat.id), event.new_chat_member.user.id, now, notify_bonus_lost)
        except Exception as e:
            logger.error(e, 'Channel bonus: cannot handle a membership change', event.chat.id)

    return router
