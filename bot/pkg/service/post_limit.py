"""How many posts a member may make in a group per day or week (a paid setting of the group), counted in Redis."""
import datetime

from framework.repository.storage_connection import Storage

PERIODS = ('day', 'week')
# The limits the group page cycles through: off, then (count, period)
CHOICES: list[tuple[int, str] | None] = [None, (1, 'day'), (2, 'day'), (3, 'day'), (5, 'day'), (1, 'week'), (3, 'week')]


def window_start(period: str, now: datetime.datetime | None = None) -> datetime.datetime:
    """The start of the current counting window, in UTC: today, or this week's Monday."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == 'week':
        start -= datetime.timedelta(days=start.weekday())
    return start


def next_window(period: str, now: datetime.datetime | None = None) -> datetime.datetime:
    return window_start(period, now) + datetime.timedelta(days=7 if period == 'week' else 1)


class PostLimit:
    @staticmethod
    def _key(chat_service_id: int, user_service_id: int, period: str, now: datetime.datetime | None) -> str:
        return f"post_limit:{chat_service_id}:{user_service_id}:{period}:{window_start(period, now).date()}"

    @staticmethod
    def take(chat_service_id: int, user_service_id: int, limit: int, period: str,
             now: datetime.datetime | None = None) -> bool:
        """Counts a post; False when it is over the limit (and then it does not count)."""
        connection = Storage().connection
        key = PostLimit._key(chat_service_id, user_service_id, period, now)
        used = connection.incr(key)
        if used == 1:
            connection.expire(key, 8 * 86400)
        if used > limit:
            connection.decr(key)
            return False
        return True

    @staticmethod
    def give_back(chat_service_id: int, user_service_id: int, period: str, now: datetime.datetime | None = None):
        """A counted post that did not stay (deleted by Telegram's refusal and so on) does not use the limit up."""
        connection = Storage().connection
        key = PostLimit._key(chat_service_id, user_service_id, period, now)
        if int(connection.get(key) or 0) > 0:
            connection.decr(key)
