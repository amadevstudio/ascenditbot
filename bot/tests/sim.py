"""The bot without Telegram, step by step: send messages, tap buttons, write in groups, and see what each step
makes the bot do. The same bench as the tests (real dispatcher, test Postgres and Redis, fake Telegram).

    ./scripts/sim.sh -c "send /start" -c "tap Начнём" -c "tap Мои группы"
    ./scripts/sim.sh scenario.txt

Actions, one per -c or per line of a file (# starts a comment):

    user ID [LANG] [NICK]   act as this user from now on (default: 501 ru owner)
    send TEXT               a message in private to the bot
    tap TEXT | tap R,C      a button of the latest message with buttons in private (by text or position)
    data JSON               a button with this callback data
    group ID                a group in Telegram: the current user its creator, the bot an admin
    connect ID              the same, connected to the current user in the bot
    paid                    the current user on tariff 1 for 30 days
    admin                   the current user is a bot admin
    in ID TEXT              the current user writes TEXT in the group (/allow in reply: see reply)
    reply ID USER TEXT      the current user replies TEXT in the group to a message of user USER
    promote ID              the current user makes the bot an admin of the group (my_chat_member)
    sql QUERY               runs a query on the test database and prints the rows
    round                   the hourly round (tariffs, expiring access)
    screen                  the last messages in the current user's private chat
"""
import asyncio
import datetime
import json
import os
import shlex
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.bench import BOT_USER, Bench, administrator, member, person  # noqa: E402


class Sim:
    def __init__(self, bench: Bench):
        self.bench = bench
        self.user = person(501, 'owner', 'ru')
        self.screens: dict[int, dict[int, dict]] = {}  # chat id -> message id -> {text, buttons}
        self.seen = 0
        original = bench.telegram.make_request

        async def recording(bot, method, timeout=None):
            result = await original(bot, method, timeout)
            self._remember(method, result)
            return result

        bench.telegram.make_request = recording

    def _remember(self, method, result):
        name = method.__api_method__
        if name not in ('sendMessage', 'sendPhoto', 'editMessageText', 'editMessageReplyMarkup'):
            return
        chat_id = int(method.chat_id) if getattr(method, 'chat_id', None) is not None else self.user['id']
        message_id = getattr(result, 'message_id', None) or getattr(method, 'message_id', None)
        screen = self.screens.setdefault(chat_id, {})
        entry = screen.setdefault(message_id, {'text': '', 'buttons': []})
        text = getattr(method, 'text', None) or getattr(method, 'caption', None)
        if text is not None:
            entry['text'] = text
        markup = getattr(method, 'reply_markup', None)
        if name == 'editMessageReplyMarkup' or markup is not None or name == 'editMessageText':
            entry['buttons'] = [[b for b in row] for row in (getattr(markup, 'inline_keyboard', None) or [])]

    # Output

    def _print_new_calls(self):
        for call in self.bench.telegram.calls[self.seen:]:
            name = call.__api_method__
            if name in ('getChatMember', 'getChat', 'getChatAdministrators', 'getMe'):
                continue
            where = getattr(call, 'chat_id', '')
            if name in ('sendMessage', 'sendPhoto', 'editMessageText'):
                text = getattr(call, 'text', None) or getattr(call, 'caption', None) or ''
                extra = ''
                if getattr(call, 'ephemeral_message_parameters', None):
                    extra = f' (only {call.ephemeral_message_parameters.receiver_user_id} sees it)'
                print(f'  {name} -> {where}{extra}')
                for line in text.splitlines():
                    print(f'    | {line}')
                self._print_markup(getattr(call, 'reply_markup', None))
            elif name == 'answerCallbackQuery':
                print(f"  toast{' (alert)' if call.show_alert else ''}: {call.text or ''}")
            elif name == 'deleteMessage':
                print(f'  deleteMessage {where} #{call.message_id}')
            elif name == 'restrictChatMember':
                state = 'unmuted' if call.permissions.can_send_messages else f'muted until {call.until_date}'
                print(f'  restrictChatMember {where} user {call.user_id}: {state}')
            else:
                print(f'  {name} {where}')
        self.seen = len(self.bench.telegram.calls)

    @staticmethod
    def _print_markup(markup):
        rows = getattr(markup, 'inline_keyboard', None)
        if rows:
            for r, row in enumerate(rows):
                print('    ' + '  '.join(f'[{r},{c} {b.text}]' for c, b in enumerate(row)))
        keyboard = getattr(markup, 'keyboard', None)
        if keyboard:
            for row in keyboard:
                print('    ' + '  '.join(f'<{b.text}>' for b in row))

    # Actions

    def _latest_buttons(self) -> list[list]:
        for message_id in sorted(self.screens.get(self.user['id'], {}), reverse=True):
            buttons = self.screens[self.user['id']][message_id]['buttons']
            if buttons:
                return buttons
        raise ValueError('no message with buttons in this chat')

    def _group_chat(self, chat_id: int) -> dict:
        return {'id': chat_id, 'type': 'supergroup', 'title': f'Group {chat_id}'}

    async def _owner_row(self) -> dict:
        rows = await self.bench.sql('SELECT * FROM users WHERE service_id = $1', str(self.user['id']))
        return rows[0] if rows else await self.bench.owner(self.user)

    async def run(self, line: str):
        words = shlex.split(line, posix=True) if line.split()[0] in ('reply',) else line.split(maxsplit=1)
        action, rest = words[0], (words[1] if len(words) > 1 else '')
        print(f'>>> {line}')
        bench = self.bench

        if action == 'user':
            parts = rest.split()
            self.user = person(int(parts[0]), parts[2] if len(parts) > 2 else None,
                               parts[1] if len(parts) > 1 else 'en')
        elif action == 'send':
            await bench.private_message(self.user, rest)
        elif action == 'tap':
            buttons = self._latest_buttons()
            if ',' in rest and rest.replace(',', '').strip().isdigit():
                r, c = (int(x) for x in rest.split(','))
                button = buttons[r][c]
            else:
                flat = [b for row in buttons for b in row]
                button = next((b for b in flat if b.text == rest), None) or next(
                    (b for b in flat if rest.lower() in b.text.lower()), None)
                if button is None:
                    raise ValueError(f'no button {rest!r} in ' + ', '.join(b.text for b in flat))
            if button.url:
                print(f'  (a link: {button.url})')
            else:
                await bench.tap(self.user, button.callback_data)
        elif action == 'data':
            await bench.tap(self.user, rest)
        elif action in ('group', 'connect'):
            chat_id = int(rest)
            owner = await self._owner_row()
            if action == 'group':
                bench.group_in_telegram(chat_id, owner)
            else:
                await bench.group(chat_id, owner)
        elif action == 'paid':
            await self._owner_row()
            await bench.sql("UPDATE user_tariff_connections SET tariff_id = 1, "
                            "end_date = LOCALTIMESTAMP + interval '30 days' "
                            "WHERE user_id = (SELECT id FROM users WHERE service_id = $1)", str(self.user['id']))
        elif action == 'admin':
            await self._owner_row()
            await bench.sql('UPDATE users SET is_admin = TRUE WHERE service_id = $1', str(self.user['id']))
        elif action == 'in':
            chat_id, text = rest.split(maxsplit=1)
            await bench.group_message(int(chat_id), self.user, text)
        elif action == 'reply':
            chat_id, author_id, text = int(words[1]), int(words[2]), words[3]
            author = person(author_id, f'user{author_id}')
            await bench.group_message(chat_id, self.user, text, reply_to_message={
                'message_id': 9999, 'date': int(datetime.datetime.now().timestamp()),
                'chat': self._group_chat(chat_id), 'from': author, 'text': 'hello'})
        elif action == 'promote':
            chat_id = int(rest)
            bench.telegram.members[(chat_id, BOT_USER['id'])] = administrator(BOT_USER)
            await bench.feed({'my_chat_member': {
                'chat': self._group_chat(chat_id), 'from': self.user,
                'date': int(datetime.datetime.now().timestamp()),
                'old_chat_member': member(BOT_USER), 'new_chat_member': administrator(BOT_USER)}})
        elif action == 'sql':
            for row in await bench.sql(rest):
                print('  ', {k: (str(v) if isinstance(v, datetime.datetime) else v) for k, v in row.items()})
        elif action == 'round':
            from pkg.background.async_tasks.subscription_handler import subscription_handler_round
            await subscription_handler_round()
        elif action == 'screen':
            for message_id, entry in sorted(self.screens.get(self.user['id'], {}).items())[-5:]:
                print(f'  #{message_id}')
                for text_line in entry['text'].splitlines():
                    print(f'    | {text_line}')
                for r, row in enumerate(entry['buttons']):
                    print('    ' + '  '.join(f'[{r},{c} {b.text}]' for c, b in enumerate(row)))
        else:
            raise ValueError(f'unknown action {action!r}')
        self._print_new_calls()


async def main(argv: list[str]) -> int:
    lines = []
    args = iter(argv)
    for arg in args:
        if arg == '-c':
            lines.append(next(args))
        else:
            with open(arg, encoding='utf-8') as file:
                lines += [line.strip() for line in file]
    lines = [line for line in lines if line and not line.startswith('#')]
    if not lines:
        print(__doc__)
        return 1

    bench = await Bench.start()
    await bench.reset()
    sim = Sim(bench)
    for line in lines:
        try:
            await sim.run(line)
        except Exception as e:
            print(f'  ERROR {type(e).__name__}: {e}')
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main(sys.argv[1:])))
