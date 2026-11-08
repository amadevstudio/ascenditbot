"""Where people come from: links t.me/<bot>?start=src_<tag> that the bot's owner makes in the admin pages. A /start
by such a link is a touch, and the first source of a new user (users.first_source); the reports follow those users
for 30 days (pkg/repository/attribution_repository.py). A /start with a tag nobody made is no source."""
import re

from pkg.repository import attribution_repository
from project import constants

# A start parameter is A-Za-z0-9_- in Telegram; "_" splits the parameter's name off, users.first_source holds 32
TAG = re.compile(r'[a-z0-9-]{1,32}')


class Attribution:
    @staticmethod
    def link(tag: str) -> str:
        return f"https://t.me/{constants.bot_nickname}?start=src_{tag}"

    @staticmethod
    def tag_of(text: str) -> str | None:
        """What the owner typed for a new source: the tag, src_<tag> or the whole link; lower case."""
        tag = re.sub(r'^.*start=', '', text.strip().lower()).removeprefix('src_')
        return tag if TAG.fullmatch(tag) else None

    @staticmethod
    async def source_of(tag: str | None) -> str | None:
        """The tag when the owner made its link, otherwise no source."""
        return tag if tag is not None and await attribution_repository.is_source(tag) else None
