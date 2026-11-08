# Tests: the bot without Telegram

```sh
./scripts/test.sh            # all cases, in throwaway containers, removed after
./scripts/test.sh notice     # only the cases whose name or description has "notice"
```

The real bot runs: the dispatcher with the routers `init_routes` registers (filters, middlewares, order), the
controllers, services and repositories, against a real Postgres built by all the migrations (so the tariffs,
prices and currencies are the seeded ones) and a real Redis. Only the Bot API is fake: `FakeTelegram` in
`bench.py` replaces the bot's HTTP session, records every request and answers as the Bot API would. Nothing
reaches Telegram, nothing is published, no secrets are needed. CI runs the same script on every pull request and
before each deploy.

| Edge | In production | In the bench |
|------|---------------|--------------|
| Updates in | long polling | `bench.group_message`, `bench.private_message`, `bench.tap` feed the dispatcher |
| Requests out | aiohttp to api.telegram.org | `bench.telegram.calls`; `calls_of('deleteMessage')`, `texts_to(chat_id)` |
| What Telegram knows | the real chats and admins | `telegram.chats`, `telegram.members`, set by `bench.group_in_telegram` |
| Telegram errors | as they come | `telegram.answers['deleteMessage'] = lambda m: TelegramBadRequest(m, '...')` |
| Database, Redis | the production ones | throwaway, emptied before each case (`bench.reset`) |

Product Hunt attribution uses the allowlisted `src_ph2` marker and records only starts carrying that marker. The
immutable `users.first_source` label is retained as a cohort label; detailed attribution events are deleted after
12 months by the existing hourly subscription task. The funnel uses a 30-day registration window. A group
participant's posting-access payments are not subscription sales.

## A case

Any `async def test_*(bench)` in `tests/test_*.py`; its docstring is what the run prints.

```python
async def test_paused_group_ignored(bench: Bench):
    """a group the owner paused is not moderated"""
    owner = await bench.owner(OWNER)                 # registered, on the free tariff
    await bench.group(GROUP, owner, active=False)    # connected through Chat.add, then paused
    await bench.group_message(GROUP, STRANGER)
    assert not bench.telegram.calls_of('deleteMessage', 'restrictChatMember', 'sendMessage')
```

## What it does not show

How Telegram renders a message or an ephemeral notice, real payments (Robokassa's HTTP callback, Stars
invoices: the handlers after them are called directly), the background subscription task, load. For those, the
bot itself in a real Telegram client.
