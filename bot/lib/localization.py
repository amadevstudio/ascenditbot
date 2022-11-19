from project.i18n import routed_messages

# panic_language = "en"
panic_language = "ru"


def get_language(lang_code: str):
    # Иногда language_code может быть None
    if not lang_code:
        return panic_language

    if "-" in lang_code:
        lang_code = lang_code.split("-")[0]

    lang_codes = {
        "ru": "ru",
        # "en": "en"
    }
    if lang_code in lang_codes:
        return lang_codes[lang_code]
    else:
        return panic_language


def get_message(message_route: [str], lang_code: str):
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
        except AttributeError:
            msg = str(' '.join(message_route))

    if msg is None:
        msg = ""

    return msg
