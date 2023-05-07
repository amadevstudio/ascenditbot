from pkg.config.config import empty_photo_link
from project.i18n import routed_messages, local_lang_based_links, emoji_codes

panic_language = "en"
# panic_language = "ru"


def get_language(lang_code: str | None):
    # Иногда language_code может быть None
    if not lang_code:
        return panic_language

    if "-" in lang_code:
        lang_code = lang_code.split("-")[0]

    lang_codes = [
        "ru",
        "en"
    ]
    if lang_code in lang_codes:
        return lang_code
    else:
        return panic_language


def get_message(message_route: [str | int], lang_code: str, **kwargs) -> str:
    lang_code = get_language(lang_code)
    curr_route = None
    msg = None
    if len(message_route) > 0:
        try:
            for r in message_route:
                if isinstance(r, str):
                    r = r.lower()
                if curr_route is None:
                    curr_route = routed_messages.get(r)
                else:
                    curr_route = curr_route.get(r)
            try:
                msg = curr_route.get(lang_code)
            except AttributeError:
                msg = curr_route.get(panic_language)

            if len(kwargs) > 0:
                try:
                    msg = msg.format(**kwargs)
                except AttributeError:
                    pass

        except AttributeError:
            msg = str(' '.join([str(route) for route in message_route]))

    if msg is None:
        msg = ""

    return msg


def get_numerical_declension_message(message_route: [str | int], lang_code: str, number: int, **kwargs) -> str:
    lang_code = get_language(lang_code)
    curr_route = None
    msg = None
    if len(message_route) > 0:
        try:
            for r in message_route:
                if curr_route is None:
                    curr_route = routed_messages.get(r.lower())
                else:
                    curr_route = curr_route.get(r.lower())
            try:
                msg = curr_route.get(lang_code)
            except AttributeError:
                msg = curr_route.get(panic_language)

            number = abs(number)
            number %= 100

            if 5 <= number <= 20:
                msg = msg[5]
            else:
                number %= 10
                if number == 1:
                    msg = msg[1]
                elif 2 <= number <= 4:
                    msg = msg[2]
                else:
                    msg = msg[5]

            if len(kwargs) > 0:
                try:
                    msg = msg.format(**kwargs)
                except AttributeError:
                    pass

        except AttributeError:
            msg = str(' '.join(message_route))

    if msg is None:
        msg = ""

    return msg


def get_link(link_route: [str | int], lang_code: str):
    lang_code = get_language(lang_code)
    curr_route = None
    link = None
    if len(link_route) > 0:
        try:
            for r in link_route:
                if curr_route is None:
                    curr_route = local_lang_based_links.get(r.lower())
                else:
                    curr_route = curr_route.get(r.lower())

            try:
                link = curr_route.get("template").format(language_code=lang_code)
            except AttributeError:
                link = curr_route.get("default")
        except AttributeError:
            link = empty_photo_link

    if link is None:
        link = empty_photo_link

    return link


def get_emoji(name):
    return emoji_codes.get(name, name)