"""Admin, Sources: the links t.me/<bot>?start=src_<tag> (pkg/service/attribution.py), each with the starts by it and
the 30-day funnel of the new users it brought; the users who came without a link, for comparison."""
import html

from framework.controller.message_tools import go_back_inline_markup, is_call_or_command, message_sender, notify
from framework.controller.types import ControllerParams
from pkg.repository import attribution_repository
from pkg.repository.attribution_repository import UNTAGGED
from pkg.service.attribution import Attribution
from pkg.service.tariff import Tariff
from pkg.service.user_storage import UserStorage

UNTAGGED_NAME = "Без метки"


def format_funnel(tag: str, stats: dict) -> str:
    def amounts(values: list[dict]) -> str:
        return ", ".join(
            f"{row['count']} на {Tariff.format_amount(row['amount'], row['minor_units'])} {row['currency_code']}"
            for row in values)

    def funnel_lines(label: str, window: dict) -> list[str]:
        paid = window['paid_by_currency'] or []
        refunds = window['refunds_by_currency'] or []
        return [
            f"<b>{label}</b>",
            f"Новые регистрации за период: {window['registrations']}",
            f"Уникальные владельцы с группой: {window['owners_connected']}; "
            f"групп подключено: {window['groups_connected']}",
            f"Уникальные владельцы с реальным списанием за тариф: {window['owners_paid']}",
            "Списания за тариф: " + (amounts(paid) if paid else "нет"),
            "Возвраты пополнений баланса (отдельно): " + (amounts(refunds) if refunds else "нет"),
        ]

    current, mature = stats['current'], stats['mature']
    if tag == UNTAGGED:
        lines = [f"<b>{UNTAGGED_NAME} · последние 12 месяцев</b>",
                 "Пришли не по ссылке-источнику: для сравнения с ними.", ""]
    else:
        lines = [
            f"<b>{html.escape(tag)} · последние 12 месяцев</b>",
            "Ссылки партнёров Telegram: <code>t.me/…?start=_tgr_…</code>, у каждого партнёра своя"
            if tag == Attribution.AFFILIATE else f"Ссылка: <code>{html.escape(Attribution.link(tag))}</code>",
            f"Стартов по ссылке: {stats['starts']}; новых пользователей при старте: {stats['new_starters']}; "
            f"существовавших ранее: {stats['returning_starters']} (это касания, не новые регистрации).",
            "",
        ]
    lines += [*funnel_lines("На сегодня · предварительный результат, окно конверсии ещё не закрыто", current), ""]
    if mature['registrations'] == 0:
        lines.append("<b>Полные 30 дней</b>")
        lines.append("Пока нет пользователей с полным 30-дневным окном.")
    else:
        lines.extend(funnel_lines("Полные 30 дней", mature))
    return "\n".join(lines)


async def list_page(params: ControllerParams):
    sources = await attribution_repository.sources()
    lines = ["<b>Источники</b> · последние 12 месяцев", ""]
    if not sources:
        lines.append("Пока ни одной ссылки.")
    for number, source in enumerate(sources, 1):
        lines.append(f"{number}. {html.escape(source['tag'])}: стартов {source['starts']}, "
                     f"новых пользователей {source['registrations']}")
    lines += [f"{UNTAGGED_NAME}: новых пользователей {await attribution_repository.untagged_registrations()}", "",
              "Старт по ссылке с меткой, которой нет в списке, не считается."]
    buttons = [[{'text': f"🔗 {source['tag']}", 'callback_data': {'tp': 'admin_source', 't': source['tag']}}]
               for source in sources]
    buttons += [[{'text': UNTAGGED_NAME, 'callback_data': {'tp': 'admin_source', 't': UNTAGGED}}],
                [{'text': "➕ Добавить источник", 'callback_data': {'tp': 'admin_add_source'}}],
                *go_back_inline_markup(params['language_code'])]
    await message_sender(params['message'].chat.id, message_structures=[{
        'type': 'text', 'text': "\n".join(lines), 'parse_mode': 'HTML', 'reply_markup': buttons}])


async def source_page(params: ControllerParams):
    message, tag = params['message'], str(params['state_data'].get('t') or UNTAGGED)
    UserStorage.add_user_state_data(message.chat.id, params['route_name'], {'t': tag})
    buttons = [] if tag == UNTAGGED else [[{'text': f"🗑 Убрать {tag}", 'callback_data': {'tp': 'admin_delete_source'}}]]
    await message_sender(message.chat.id, message_structures=[{
        'type': 'text', 'text': format_funnel(tag, await attribution_repository.funnel(tag)), 'parse_mode': 'HTML',
        'reply_markup': [*buttons, *go_back_inline_markup(params['language_code'])]}])


async def delete_source(params: ControllerParams):
    """New starts by the link stop counting; the users it brought keep it as their first source."""
    tag = str(params['state_data'].get('t'))
    removed = await attribution_repository.delete_source(tag)
    await notify(params['call'], params['message'], f"Убран: {tag}" if removed else "Уже убран")
    await params['go_back_action'](params['call'])


async def add_source(params: ControllerParams):
    """"➕ Добавить источник": the bot waits for the tag; it may come as src_<tag> or the whole link."""
    call, message, language_code = params['call'], params['message'], params['language_code']
    hint = "латиница, цифры, дефис, до 32 знаков"
    if is_call_or_command(call, message):
        await message_sender(message.chat.id, message_structures=[{
            'type': 'text', 'parse_mode': 'HTML',
            'text': f"Пришлите метку источника: {hint}. Например, <code>reddit</code>: ссылка будет "
                    f"<code>{html.escape(Attribution.link('reddit'))}</code>",
            'reply_markup': go_back_inline_markup(language_code)}])
        return

    tag = Attribution.tag_of(message.text or '')
    if tag is None:
        await notify(None, message, f"Не подходит: нужна метка, {hint}. Пришлите другую.", save_state=True)
        return
    await attribution_repository.add_source(tag)
    await message_sender(message.chat.id, message_structures=[{
        'type': 'text', 'parse_mode': 'HTML',
        'text': f"✅ Источник <b>{html.escape(tag)}</b> добавлен. Ссылка:\n"
                f"<code>{html.escape(Attribution.link(tag))}</code>\n\nПришлите ещё метку или вернитесь назад.",
        'reply_markup': go_back_inline_markup(language_code)}])
