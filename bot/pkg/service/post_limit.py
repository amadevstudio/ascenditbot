"""How many posts a member may make in a group: no more than `count` in any `hours` hours (a paid setting of the
group). Admins are not limited. Counted in Redis, one sorted set of post times per member and group.

The owner picks one of the usual limits or types their own the way people say it: "3 в час", "10 за 2 дня",
"1 a week", "5/6h"; "выкл" removes it."""
import datetime
import re
import time
import uuid

from framework.repository.storage_connection import Storage
from lib.language import localization

MAX_COUNT = 100
MAX_HOURS = 30 * 24
# The usual limits, (count, hours), offered as buttons
CHOICES: list[tuple[int, int]] = [(1, 1), (1, 24), (3, 24), (5, 24), (1, 168), (3, 168)]
OFF = 'off'

_OFF_WORDS = {'выкл', 'выключить', 'нет', 'убрать', 'без', 'off', 'no', 'none', '0', '-'}
_FILLERS = {'в', 'во', 'за', 'на', 'раз', 'сообщение', 'сообщения', 'сообщений', 'пост', 'поста', 'постов',
            'per', 'a', 'an', 'in', 'every', 'each', 'post', 'posts', 'message', 'messages', 'times', 'time'}
_UNITS = {}
for _words, _hours in (
        (('ч', 'час', 'часа', 'часов', 'h', 'hr', 'hrs', 'hour', 'hours'), 1),
        (('д', 'дн', 'день', 'дня', 'дней', 'сут', 'сутки', 'суток', 'd', 'day', 'days'), 24),
        (('нед', 'неделю', 'неделя', 'недели', 'недель', 'w', 'wk', 'week', 'weeks'), 168),
        (('мес', 'месяц', 'месяца', 'месяцев', 'mo', 'month', 'months'), 720)):
    for _word in _words:
        _UNITS[_word] = _hours


def parse_limit(text: str) -> tuple[int, int] | str | None:
    """(count, hours) from the owner's words, OFF to remove the limit, None when it is not a limit."""
    line = (text or '').lower().replace('/', ' / ')
    line = re.sub(r'(?<=\d)(?=[^\d\s])|(?<=[^\d\s])(?=\d)', ' ', line)
    tokens = [token for token in re.split(r'[\s,.:;–—-]+', line) if token]
    if not tokens or (tokens[0] in _OFF_WORDS and len(tokens) <= 2):
        return OFF if tokens else None
    tokens = [token for token in tokens if token not in _FILLERS and token != '/']
    if not tokens or not tokens[0].isdigit():
        return None
    count, tokens = int(tokens[0]), tokens[1:]
    window = 1
    if tokens and tokens[0].isdigit():
        window, tokens = int(tokens[0]), tokens[1:]
    if len(tokens) != 1 or tokens[0] not in _UNITS:
        return None
    hours = window * _UNITS[tokens[0]]
    if count == 0:
        return OFF
    if not 1 <= count <= MAX_COUNT or not 1 <= hours <= MAX_HOURS:
        return None
    return count, hours


def _plural(number: int, language_code: str | None) -> str:
    if (language_code or '').lower().startswith('ru'):
        if number % 10 == 1 and number % 100 != 11:
            return 'one'
        if number % 10 in (2, 3, 4) and number % 100 not in (12, 13, 14):
            return 'few'
        return 'many'
    return 'one' if number == 1 else 'many'


def limit_text(count: int | None, hours: int | None, language_code: str | None) -> str:
    """"3 в день", "10 за 6 часов", "1 a week"; "без лимита" when there is none."""
    if not count or not hours:
        return localization.get_message(['chat', 'show', 'limit', 'off'], language_code)
    unit, window = next((unit, hours // size) for unit, size in (('week', 168), ('day', 24), ('hour', 1))
                        if hours % size == 0)
    if window == 1:
        return localization.get_message(['chat', 'show', 'limit', 'per', unit], language_code, limit=count)
    return localization.get_message(['chat', 'show', 'limit', 'within', unit, _plural(window, language_code)],
                                    language_code, limit=count, window=window)


def of_chat(chat: dict) -> tuple[int, int] | None:
    count, hours = chat.get('post_limit'), chat.get('post_limit_hours')
    return (count, hours) if count and hours else None


class PostLimit:
    @staticmethod
    def _key(chat_service_id: int, user_service_id: int) -> str:
        return f"post_limit:{chat_service_id}:{user_service_id}"

    @staticmethod
    def take(chat_service_id: int, user_service_id: int, count: int, hours: int,
             now: float | None = None) -> datetime.datetime | None:
        """Counts a post. None when it fits the limit; otherwise (not counted) when the next one will."""
        connection = Storage().connection
        key = PostLimit._key(chat_service_id, user_service_id)
        now = time.time() if now is None else now
        window = hours * 3600
        connection.zremrangebyscore(key, '-inf', now - window)
        if connection.zcard(key) >= count:
            oldest = connection.zrange(key, -count, -count, withscores=True)
            at = (oldest[0][1] if oldest else now) + window
            return datetime.datetime.fromtimestamp(at, datetime.timezone.utc)
        connection.zadd(key, {f'{now}:{uuid.uuid4().hex[:8]}': now})
        connection.expire(key, window + 60)
        return None
