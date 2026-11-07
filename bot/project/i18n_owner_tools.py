"""Texts of the owner tools: the group page, timed access, posting limits, alerts to the group's managers,
commands in the group, and the onboarding that leads to them. Merged into routed_messages by project.i18n.

Keys are lower case (get_message lowers the route). Which texts are HTML is said next to them."""
from project import constants

_bot = constants.bot_nickname
ADD_TO_GROUP_URL = f"https://t.me/{_bot}?startgroup=connect&admin=delete_messages+restrict_members+pin_messages"
# How it all works, with screenshots: posts in the bot's channel
GUIDE_URLS = {'en': "https://t.me/ascendit_group/21", 'ru': "https://t.me/ascendit_group/13"}


def guide_url(language_code: str | None) -> str:
    return GUIDE_URLS['ru' if (language_code or '').lower().startswith('ru') else 'en']

owner_tools_messages = {
    'welcome': {
        'introduction': {
            'en':
                "Hi! I keep your group clean: only the people you allow can write in it, everyone else's "
                "messages are deleted at once.\n\n"
                "Made for groups of ads and announcements, where the right to post is worth something:\n"
                "● a whitelist by nickname, id or a forwarded message\n"
                "● access for 7 or 30 days, ending on its own\n"
                "● a posting limit: 1 ad a day, 3 an hour, 10 in 2 days\n"
                "● a message when a stranger writes, with \"Allow\" in one tap\n"
                "● outsiders ask you for access or pay for it, you confirm in one tap\n\n"
                "One group is free.",
            'ru':
                "Привет! Я слежу за порядком в группе: писать в ней могут только те, кого вы разрешили, "
                "остальные сообщения сразу удаляются.\n\n"
                "Сделан для групп объявлений и рекламы, где право писать чего-то стоит:\n"
                "● белый список по нику, id или пересланному сообщению\n"
                "● доступ на 7 или 30 дней, который сам заканчивается\n"
                "● лимит постов: 1 объявление в день, 3 в час, 10 за 2 дня\n"
                "● сообщение, когда пишет посторонний, и \"Разрешить\" в одно нажатие\n"
                "● посторонние просят доступ или платят вам, вы подтверждаете в одно нажатие\n\n"
                "Одна группа бесплатно."
        },
    },
    'help': {
        'text': {
            'en':
                f"@{_bot} lets only the people you allow write in your group.\n\n"
                "<b>Connect a group</b>: /add_chat, then \"Select a group\" and pick it: Telegram adds the bot "
                "as an admin with the rights it needs.\n\n"
                "<b>Manage it</b>: /my_chats. On the group's page: the whitelist, who may write (the whitelist or "
                "everyone), whether admins are checked too, the posting limit, how long offenders stay muted.\n\n"
                "<b>Outsiders</b> (someone off the whitelist writes): on the group's page, \"🚪 Outsiders\". "
                "The bot deletes the message and then does nothing more, tells you (with \"Allow\"), lets them "
                "ask for access, or sells it for a term (paid tariffs). You confirm in one tap.\n\n"
                "<b>Right in the group</b> (admins only, nobody else sees the answers):\n"
                "/allow in reply to a message, or /allow @nick 7d – let a member write (for 7 days)\n"
                "/deny @nick – take them off the list\n"
                "/settings – open the group's page here\n\n"
                "<b>Free</b>: one group with a whitelist and alerts. <b>Paid</b> (/subscription): more groups, "
                "access for a term and posting limits.\n\n"
                "Questions and ideas: the button below, we answer in person.",
            'ru':
                f"@{_bot} разрешает писать в группе только тем, кого вы допустили.\n\n"
                "<b>Подключить группу</b>: /add_chat, затем \"Выбрать группу\" и выберите её: Telegram сам "
                "добавит бота администратором с нужными правами.\n\n"
                "<b>Управлять</b>: /my_chats. На странице группы: белый список, кто пишет (белый список или все), "
                "проверять ли админов, лимит постов, мут нарушителей.\n\n"
                "<b>Посторонние</b> (пишет тот, кого нет в белом списке): на странице группы, \"🚪 Посторонние\". "
                "Бот удаляет сообщение, а дальше молчит, сообщает вам (с кнопкой \"Разрешить\"), даёт попросить "
                "доступ или продаёт его на срок (платные тарифы). Вы подтверждаете в одно нажатие.\n\n"
                "<b>Прямо в группе</b> (только админам, ответы видите только вы):\n"
                "/allow в ответ на сообщение или /allow @nick 7d – разрешить писать (на 7 дней)\n"
                "/deny @nick – убрать из списка\n"
                "/settings – открыть страницу группы здесь\n\n"
                "<b>Бесплатно</b>: одна группа с белым списком и оповещениями. <b>Платно</b> (/subscription): "
                "больше групп, доступ на срок и лимиты постов.\n\n"
                "Вопросы и идеи: кнопка ниже, отвечаем лично."
        },
        'contact_button': {'en': "💬 Write to us", 'ru': "💬 Написать нам"},
        'guide_button': {'en': "📖 How it works", 'ru': "📖 Как пользоваться"},
    },
    'add_chat': {
        # HTML
        'instruction': {
            'en':
                "<b>Connect a group</b>\n\n"
                "Tap <b>➕ Select a group</b> at the bottom of the screen and pick it. Telegram adds the bot as an "
                "admin with the rights it needs, and the bot sends you the group's page. That's all.\n\n"
                "The bot asks to:\n"
                "● delete messages – of those you have not allowed\n"
                "● restrict members – to mute offenders for a few minutes\n"
                "● pin messages – to pin the \"Get access\" button, if you use it\n\n"
                "No button at the bottom (Telegram on a computer sometimes hides it)? Use \"Add to a group\" "
                "below: it does the same.",
            'ru':
                "<b>Подключить группу</b>\n\n"
                "Нажмите <b>➕ Выбрать группу</b> внизу экрана и выберите её. Telegram сам добавит бота "
                "администратором с нужными правами, а бот пришлёт страницу группы. Это всё.\n\n"
                "Бот просит права:\n"
                "● удалять сообщения – тех, кому вы не разрешили писать\n"
                "● ограничивать участников – чтобы на несколько минут мутить нарушителей\n"
                "● закреплять сообщения – чтобы закрепить кнопку \"Получить доступ\", если она вам нужна\n\n"
                "Кнопки внизу нет (Telegram на компьютере иногда её прячет)? Нажмите \"Добавить в группу\" "
                "ниже: это то же самое."
        },
        'add_to_group_button': {
            'en': "➕ Add to a group",
            'ru': "➕ Добавить в группу"
        },
        'add_chat_reply_button_text': {
            'en': "👇 Pick the group with the button below",
            'ru': "👇 Выберите группу кнопкой внизу"
        },
        'add_chat_reply_button': {
            'en': "➕ Select a group",
            'ru': "➕ Выбрать группу"
        },
        'success': {
            'en': "Group {chat_name} is connected!",
            'ru': "Группа {chat_name} подключена!"
        },
        'errors': {
            'connection_exists': {
                'en': "This group is already connected.",
                'ru': "Эта группа уже подключена."
            },
        }
    },
    'chat': {
        # The group's page, HTML
        'show': {
            'state': {
                'on': {
                    'en': "✅ Moderation is on",
                    'ru': "✅ Модерация включена"
                },
                'paused': {
                    'en': "⏸ Paused: everyone can write",
                    'ru': "⏸ На паузе: писать могут все"
                },
                'disabled': {
                    'en': "⚠️ Off: the tariff does not cover this group",
                    'ru': "⚠️ Отключена: тариф не покрывает эту группу"
                },
            },
            'who': {
                'everyone': {
                    'en': "Who writes: everyone (whitelist: {count})",
                    'ru': "Кто пишет: все (в белом списке: {count})"
                },
                'whitelist': {
                    'en': "Who writes: the whitelist ({count}) and admins",
                    'ru': "Кто пишет: белый список ({count}) и админы"
                },
                'whitelist_only': {
                    'en': "Who writes: the whitelist ({count}); admins are checked too",
                    'ru': "Кто пишет: белый список ({count}), админы тоже проверяются"
                },
            },
            'limit': {
                'off': {
                    'en': "no limit",
                    'ru': "без лимита"
                },
                'per': {
                    'hour': {'en': "{limit} an hour", 'ru': "{limit} в час"},
                    'day': {'en': "{limit} a day", 'ru': "{limit} в день"},
                    'week': {'en': "{limit} a week", 'ru': "{limit} в неделю"},
                },
                'within': {
                    'hour': {
                        'one': {'en': "{limit} in {window} hour", 'ru': "{limit} за {window} час"},
                        'few': {'en': "{limit} in {window} hours", 'ru': "{limit} за {window} часа"},
                        'many': {'en': "{limit} in {window} hours", 'ru': "{limit} за {window} часов"},
                    },
                    'day': {
                        'one': {'en': "{limit} in {window} day", 'ru': "{limit} за {window} день"},
                        'few': {'en': "{limit} in {window} days", 'ru': "{limit} за {window} дня"},
                        'many': {'en': "{limit} in {window} days", 'ru': "{limit} за {window} дней"},
                    },
                    'week': {
                        'one': {'en': "{limit} in {window} week", 'ru': "{limit} за {window} неделю"},
                        'few': {'en': "{limit} in {window} weeks", 'ru': "{limit} за {window} недели"},
                        'many': {'en': "{limit} in {window} weeks", 'ru': "{limit} за {window} недель"},
                    },
                },
                'paused_free': {
                    'en': "(works on a paid tariff)",
                    'ru': "(работает на платном тарифе)"
                },
                'paid_only': {
                    'en': "Posting limits are on paid tariffs. See /subscription",
                    'ru': "Лимит постов есть на платных тарифах. Подробнее: /subscription"
                },
            },
            'limit_line': {
                'en': "Posts per member: {limit}",
                'ru': "Постов на участника: {limit}"
            },
            'removed_week': {
                'en': "Deleted in 7 days: {count}",
                'ru': "Удалено за 7 дней: {count}"
            },
            'disabled': {
                'en': "⚠️ Messages are not checked: your tariff covers fewer groups. More: /subscription",
                'ru': "⚠️ Сообщения не проверяются: тариф покрывает меньше групп. Подробнее: /subscription"
            },
            'empty_whitelist_hint': {
                'en':
                    "The whitelist is empty, so only admins can write. Add members with the button below, "
                    "or reply /allow to a message in the group.",
                'ru':
                    "Белый список пуст, поэтому писать могут только админы. Добавьте участников кнопкой ниже "
                    "или ответьте /allow на сообщение в группе."
            },
            'paid_entry_hint': {
                'en': "💡 Want people to pay for the right to write? \"🚪 Outsiders\" → \"💳 Paid\": they pick a "
                      "term and pay you, access opens and ends by itself.",
                'ru': "💡 Хотите, чтобы за право писать платили? \"🚪 Посторонние\" → \"💳 За плату\": человек "
                      "выбирает срок и платит вам, доступ открывается и заканчивается сам."
            },
            'empty_whitelist_hint_strict': {
                'en':
                    "The whitelist is empty and admins are checked too, so nobody can write, you included. Add "
                    "members with the button below, or reply /allow to a message in the group.",
                'ru':
                    "Белый список пуст, а админы тоже проверяются, поэтому писать не может никто, даже вы. "
                    "Добавьте участников кнопкой ниже или ответьте /allow на сообщение в группе."
            },
            'add_to_whitelist_button': {
                'en': "➕ Allow members",
                'ru': "➕ Разрешить писать"
            },
            'whitelist_button': {
                'en': "📋 Whitelist ({count})",
                'ru': "📋 Белый список ({count})"
            },
            'who_button': {
                'everyone': {
                    'en': "Who writes: everyone",
                    'ru': "Кто пишет: все"
                },
                'whitelist': {
                    'en': "Who writes: whitelist",
                    'ru': "Кто пишет: белый список"
                },
            },
            'locked': {
                'en': "🔒 ",
                'ru': "🔒 "
            },
            'limit_button': {
                'en': "⏱ Limit: {limit}",
                'ru': "⏱ Лимит: {limit}"
            },
            'access_button': {
                'silent': {'en': "🚪 Outsiders: 🔕 quietly", 'ru': "🚪 Посторонние: 🔕 молча"},
                'alert': {'en': "🚪 Outsiders: 🔔 tell me", 'ru': "🚪 Посторонние: 🔔 сообщать мне"},
                'request': {'en': "🚪 Outsiders: 📨 by request", 'ru': "🚪 Посторонние: 📨 по заявке"},
                'paid': {'en': "🚪 Outsiders: 💳 paid", 'ru': "🚪 Посторонние: 💳 за плату"},
            },
            'restriction_duration_button': {
                'en': "🔇 Mute offenders: {duration} min",
                'ru': "🔇 Мут нарушителю: {duration} мин"
            },
            'active_button': {
                'active': {
                    'en': "⏸ Pause moderation",
                    'ru': "⏸ Поставить на паузу"
                },
                'inactive': {
                    'en': "▶️ Turn moderation on",
                    'ru': "▶️ Включить модерацию"
                }
            },
            'who_toast': {
                'everyone': {
                    'en': "Everyone can write now. Set a posting limit, if needed",
                    'ru': "Теперь пишут все. При необходимости задайте лимит постов"
                },
                'whitelist': {
                    'en': "Only the whitelist and admins can write now",
                    'ru': "Теперь пишут только белый список и админы"
                },
            },
            'admins_button': {
                'free': {'en': "👮 Admins: not checked", 'ru': "👮 Админы: без проверки"},
                'checked': {'en': "👮 Admins: checked too", 'ru': "👮 Админы: тоже проверять"},
            },
            'admins_toast': {
                'free': {
                    'en': "Admins write without the whitelist again",
                    'ru': "Админы снова пишут без белого списка"
                },
                'checked': {
                    'en': "Admins are checked too now: off the whitelist, their messages are deleted, yours too",
                    'ru': "Теперь админов тоже проверяем: если их нет в белом списке, сообщения удаляются. "
                          "Ваши тоже"
                },
            },
        },
        # The posting limit page, HTML
        'post_limit': {
            'text': {
                'en':
                    "⏱ <b>Posting limit: {chat_name}</b>\n\n"
                    "Now: <b>{limit}</b>\n\n"
                    "Each member, the whitelist included, may post no more than that; the bot deletes the extra "
                    "posts and tells the author when the next one is possible. Admins have no limit.\n\n"
                    "Pick one or type your own: <code>3 an hour</code>, <code>10 in 2 days</code>, "
                    "<code>1 a week</code>. To remove it: <code>off</code>.",
                'ru':
                    "⏱ <b>Лимит постов: {chat_name}</b>\n\n"
                    "Сейчас: <b>{limit}</b>\n\n"
                    "Каждый участник, в том числе из белого списка, пишет не больше этого: лишнее бот удаляет и "
                    "подсказывает автору, когда можно следующее. У админов лимита нет.\n\n"
                    "Выберите или напишите свой: <code>3 an hour</code>, <code>10 in 2 days</code>, "
                    "<code>1 a week</code>. Убрать: <code>off</code>."
            },
            'free': {
                'en': "🔒 It works on a paid tariff (/subscription): you can set it now, it starts with the tariff.",
                'ru': "🔒 Работает на платном тарифе (/subscription): задать можно сейчас, заработает с тарифом."
            },
            'saved': {
                'en': "✅ Saved: {limit}",
                'ru': "✅ Сохранено: {limit}"
            },
            'invalid': {
                'en': "❌ Not a limit: {text}. Like this: <code>3 an hour</code>, <code>10 in 2 days</code>, "
                      "<code>off</code>. Up to {max_count} posts, a window up to 30 days.",
                'ru': "❌ Не похоже на лимит: {text}. Так: <code>3 an hour</code>, <code>10 in 2 days</code>, "
                      "<code>off</code>. До {max_count} постов, окно до 30 дней."
            },
            'off_button': {
                'en': "No limit",
                'ru': "Без лимита"
            },
        },
        'add_to_whitelist': {
            # HTML
            'text': {
                'en':
                    "<b>Who may write?</b>\n\n"
                    "Send nicknames, ids or t.me links, separated by spaces: <code>@anna 123456789</code>\n"
                    "Or forward a message from the member, or pick them from your contacts with the button below.\n\n"
                    "For a term, add it at the end: <code>@anna 7d</code>. It is for everyone in the message: "
                    "<code>@anna @kate 7d</code> gives both 7 days.",
                'ru':
                    "<b>Кому разрешить писать?</b>\n\n"
                    "Пришлите ники, id или ссылки t.me через пробел: <code>@anna 123456789</code>\n"
                    "Или перешлите сообщение участника, или выберите его из контактов кнопкой ниже.\n\n"
                    "На срок: добавьте его в конце, <code>@anna 7d</code>. Срок для всех в сообщении: "
                    "<code>@anna @kate 7d</code> даст 7 дней обеим."
            },
            'pick_button': {
                'en': "👤 Pick from contacts",
                'ru': "👤 Выбрать из контактов"
            },
            'pick_hint': {
                'en': "⬇️ Or pick members:",
                'ru': "⬇️ Или выберите участников:"
            },
            # Plain text
            'success_list': {
                'en': "✅ Can write now: {members}",
                'ru': "✅ Теперь могут писать: {members}"
            },
            'success_list_until': {
                'en': "✅ Can write until {date}: {members}",
                'ru': "✅ Могут писать до {date}: {members}"
            },
            'not_understood': {
                'en': "Not understood: {words}. A nickname is 4 to 32 Latin letters, digits or _; or send an id or "
                      "a t.me link",
                'ru': "Не понял: {words}. Ник – от 4 до 32 латинских букв, цифр или _; или пришлите id или ссылку "
                      "t.me"
            },
            'more': {
                'en': "Send more or go back.",
                'ru': "Пришлите ещё или вернитесь назад."
            },
        },
    },
    'allowed_user': {
        'show': {
            # HTML
            'text': {
                'en': "👥 {chat_name}\nMember: {member}",
                'ru': "👥 {chat_name}\nУчастник: {member}"
            },
            'term': {
                'forever': {
                    'en': "Access: for good",
                    'ru': "Доступ: бессрочно"
                },
                'until': {
                    'en': "Access: until {date}",
                    'ru': "Доступ: до {date}"
                },
                'ended': {
                    'en': "⌛️ Access ended {date}",
                    'ru': "⌛️ Доступ закончился {date}"
                },
                # Plain, in the list's buttons
                'until_short': {
                    'en': "until {date}",
                    'ru': "до {date}"
                },
            },
            # What the member can do now
            'state': {
                'forever': {'en': "✅ Can write, for good", 'ru': "✅ Может писать, бессрочно"},
                'until': {'en': "✅ Can write until {date}", 'ru': "✅ Может писать до {date}"},
                'off': {'en': "⏸ Switched off: their messages are deleted",
                        'ru': "⏸ Выключен: сообщения удаляются"},
                'off_until': {'en': "⏸ Switched off: their messages are deleted (the term runs until {date})",
                              'ru': "⏸ Выключен: сообщения удаляются (срок до {date})"},
                'ended': {'en': "⌛️ Access ended {date}: their messages are deleted",
                          'ru': "⌛️ Доступ закончился {date}: сообщения удаляются"},
            },
            'no_id_hint': {
                'en':
                    "Known by the nickname only: if they change it, they lose access. When they write in the "
                    "group, the bot remembers their id.",
                'ru':
                    "Известен только по нику: если сменит ник, потеряет доступ. Когда он напишет в группе, "
                    "бот запомнит его id."
            },
            'term_button': {
                'forever': {
                    'en': "For good",
                    'ru': "Бессрочно"
                },
                'days': {
                    'en': "{days} days",
                    'ru': "{days} дней"
                },
                # Added to a running term
                'extend': {
                    'en': "+{days} days",
                    'ru': "+{days} дней"
                },
            },
            'term_toast': {
                'forever': {
                    'en': "Access for good",
                    'ru': "Доступ бессрочный"
                },
                'until': {
                    'en': "Access until {date}",
                    'ru': "Доступ до {date}"
                },
            },
            'active_button': {
                'active': {'en': "⏸ Stop them writing", 'ru': "⏸ Запретить писать"},
                'inactive': {'en': "▶️ Let them write again", 'ru': "▶️ Разрешить снова"},
            },
        },
    },
    # The group's whitelist, a paged list
    'whitelist': {
        'list': {
            # HTML
            'text': {'en': "📋 <b>Whitelist</b>: {chat_name}", 'ru': "📋 <b>Белый список</b>: {chat_name}"},
            'writing': {'en': "✅ can write: {count}", 'ru': "✅ пишут: {count}"},
            'off': {'en': "⏸ switched off: {count}", 'ru': "⏸ выключены: {count}"},
            'ended': {'en': "⌛️ access ended: {count}", 'ru': "⌛️ срок истёк: {count}"},
            'search_hint': {'en': "🔎 To find someone, send a nickname, a name or an id.",
                            'ru': "🔎 Чтобы найти, пришлите ник, имя или id."},
            'search_now': {'en': "🔎 Found by \"{query}\"", 'ru': "🔎 Найдено по \"{query}\""},
            'pages': {'en': "Page {page} of {pages}: send a number to go to that page.",
                      'ru': "Страница {page} из {pages}: пришлите номер, чтобы перейти."},
            # Plain, the buttons
            'button': {
                'active': {'en': "✅ {nickname}", 'ru': "✅ {nickname}"},
                'inactive': {'en': "⏸ {nickname}", 'ru': "⏸ {nickname}"},
                'ended': {'en': "⌛️ {nickname}", 'ru': "⌛️ {nickname}"},
            },
            'ended_short': {'en': "ended {date}", 'ru': "истёк {date}"},
            'clean_button': {'en': "🧹 Remove the ended ({count})", 'ru': "🧹 Убрать истёкшие ({count})"},
            'clean_confirm_button': {'en': "⚠️ Remove {count}? Tap again", 'ru': "⚠️ Убрать {count}? Нажмите ещё раз"},
            'cleaned': {'en': "Removed: {count}", 'ru': "Убрано: {count}"},
        },
    },
    'work': {
        # Plain text, ephemeral: only the member sees it
        'limit_notice': {
            'en': "Your message was removed: members post up to {limit} here. Next one in {wait}.",
            'ru': "Сообщение удалено: здесь можно писать не больше {limit}. Следующее – через {wait}."
        },
        # How long until the next post: "45 min", "3 h 20 min", "2 d 4 h"
        'wait_units': {
            'minutes': {'en': "{n} min", 'ru': "{n} мин"},
            'hours': {'en': "{n} h", 'ru': "{n} ч"},
            'days': {'en': "{n} d", 'ru': "{n} дн."},
        },
    },
    # To the group's managers in private, HTML
    'alerts': {
        'removed': {
            'text': {
                'en': "🚫 {member} wrote in {chat_name} and is not on the whitelist. The message was deleted:",
                'ru': "🚫 {member} написал(а) в {chat_name}, но не в белом списке. Сообщение удалено:"
            },
            'no_text': {
                'en': "<i>(no text: a photo, a sticker or a file)</i>",
                'ru': "<i>(без текста: фото, стикер или файл)</i>"
            },
            'hint': {
                'en': "Let them write?",
                'ru': "Разрешить писать?"
            },
        },
        'expiry': {
            'soon': {
                'en': "⌛️ {member}'s access to {chat_name} ends {date}. Extend it?",
                'ru': "⌛️ Доступ {member} в {chat_name} закончится {date}. Продлить?"
            },
            'ended': {
                'en': "⌛️ {member}'s access to {chat_name} has ended ({date}). Their messages are deleted now.",
                'ru': "⌛️ Доступ {member} в {chat_name} закончился ({date}). Теперь сообщения удаляются."
            },
        },
        'buttons': {
            'allow_forever': {
                'en': "✅ Allow",
                'ru': "✅ Разрешить"
            },
            'allow_days': {
                'en': "For {days} days",
                'ru': "На {days} дней"
            },
            'renew_forever': {
                'en': "✅ Make it for good",
                'ru': "✅ Бессрочно"
            },
            'renew_days': {
                'en': "+{days} days",
                'ru': "+{days} дней"
            },
            'group': {
                'en': "⚙️ Group",
                'ru': "⚙️ Группа"
            },
            'mute': {
                'en': "🔕 Mute",
                'ru': "🔕 Не сообщать"
            },
            'unmute': {
                'en': "🔔 Turn alerts on",
                'ru': "🔔 Включить оповещения"
            },
            'undo': {
                'en': "↩️ Undo",
                'ru': "↩️ Отменить"
            },
        },
        'allowed': {
            'en': "✅ {member} can write in {chat_name} now.",
            'ru': "✅ {member} теперь может писать в {chat_name}."
        },
        'allowed_until': {
            'en': "✅ {member} can write in {chat_name} until {date}.",
            'ru': "✅ {member} может писать в {chat_name} до {date}."
        },
        'undone': {
            'en': "↩️ {member} is off the whitelist of {chat_name} again.",
            'ru': "↩️ {member} снова не в белом списке {chat_name}."
        },
        'muted': {
            'en': "🔕 No more alerts about {chat_name}. Turn them back on here or on the group's page.",
            'ru': "🔕 Больше не сообщаем о {chat_name}. Включить можно здесь или на странице группы."
        },
        'unmuted': {
            'en': "🔔 Alerts about {chat_name} are on.",
            'ru': "🔔 Оповещения о {chat_name} включены."
        },
        # Toasts and alerts on buttons, plain
        'allowed_toast': {
            'en': "Allowed",
            'ru': "Разрешено"
        },
        'paid_only': {
            'en': "Access for a term is on paid tariffs. See /subscription",
            'ru': "Доступ на срок есть на платных тарифах. Подробнее: /subscription"
        },
        'not_yours': {
            'en': "You no longer manage this group",
            'ru': "Вы больше не управляете этой группой"
        },
        'expired': {
            'en': "The button is too old. Open the group's page instead",
            'ru': "Кнопка устарела. Откройте страницу группы"
        },
    },
    # Answers to commands in the group, HTML, ephemeral (only the admin sees them)
    'group': {
        'not_connected': {
            'en': f"This group is not connected yet. Send /settings here to connect it, or open @{_bot}.",
            'ru': f"Группа ещё не подключена. Отправьте здесь /settings, чтобы подключить её, или откройте @{_bot}."
        },
        'usage': {
            'allow': {
                'en':
                    "Reply <code>/allow</code> to a member's message, or send <code>/allow @nick</code>. "
                    "For a term: <code>/allow @nick 7d</code>",
                'ru':
                    "Ответьте <code>/allow</code> на сообщение участника или отправьте <code>/allow @nick</code>. "
                    "На срок: <code>/allow @nick 7d</code>"
            },
            'deny': {
                'en': "Reply <code>/deny</code> to a member's message, or send <code>/deny @nick</code>",
                'ru': "Ответьте <code>/deny</code> на сообщение участника или отправьте <code>/deny @nick</code>"
            },
        },
        'allowed': {
            'en': "✅ Can write now: {members}",
            'ru': "✅ Теперь могут писать: {members}"
        },
        'allowed_until': {
            'en': "✅ Can write until {date}: {members}",
            'ru': "✅ Могут писать до {date}: {members}"
        },
        'denied': {
            'en': "🚫 Off the whitelist: {members}",
            'ru': "🚫 Убраны из белого списка: {members}"
        },
        'not_understood': {
            'en': "Not understood: {words}",
            'ru': "Не понял: {words}"
        },
        'settings_sent': {
            'en': f"The group's page is in your chat with @{_bot}.",
            'ru': f"Страница группы – в чате с @{_bot}."
        },
        'settings_link': {
            'en': "<a href=\"{link}\">Open the group's settings</a>",
            'ru': "<a href=\"{link}\">Открыть настройки группы</a>"
        },
        'register_first': {
            'en': "Start @{bot} first, then send /settings here again.",
            'ru': "Сначала запустите @{bot}, затем снова отправьте здесь /settings."
        },
        'cannot_connect': {
            'en': "Cannot connect the group: {reason}",
            'ru': "Не получилось подключить группу: {reason}"
        },
        # In private to the one who made the bot an admin, HTML
        'auto_connected': {
            'en': "✅ Group <b>{chat_name}</b> is connected. Here is its page:",
            'ru': "✅ Группа <b>{chat_name}</b> подключена. Вот её страница:"
        },
        'give_rights_button': {
            'en': "🔧 Give the bot its rights",
            'ru': "🔧 Дать боту права"
        },
        'auto_connect_failed': {
            'en': "Could not connect <b>{chat_name}</b>: {reason}",
            'ru': "Не удалось подключить <b>{chat_name}</b>: {reason}"
        },
        'needs_admin': {
            'en':
                "The bot is in <b>{chat_name}</b>, but cannot delete messages yet. Tap the button below and pick "
                "the group again: Telegram will offer the rights, ticked. Then the bot connects the group itself.",
            'ru':
                "Бот в группе <b>{chat_name}</b>, но пока не может удалять сообщения. Нажмите кнопку ниже и снова "
                "выберите группу: Telegram предложит права, уже отмеченные. После этого бот сам подключит группу."
        },
    },
    # The way in through the bot (pkg/service/access.py). HTML unless noted
    'access': {
        'chat': {
            'errors': {
                'not_registered': {
                    'en': "you have not started the bot yet",
                    'ru': "вы ещё не запускали бота"
                },
            },
            # Opening a group whose rights the owner took away: what is wrong and the one tap that fixes it
            'fix_rights': {
                'no_rights': {
                    'en': "⚠️ <b>The bot cannot delete messages in this group</b>: it is not an admin, or lacks the "
                          "right to delete. Until then nothing is moderated there.\n\nTap the button below and pick "
                          "the group: Telegram will offer the rights, already ticked. Then the group works again "
                          "and its page opens.",
                    'ru': "⚠️ <b>Бот не может удалять сообщения в этой группе</b>: он не админ или у него нет права "
                          "удалять. Пока так, модерации там нет.\n\nНажмите кнопку ниже и выберите группу: Telegram "
                          "предложит права, уже отмеченные. После этого группа снова заработает и откроется."
                },
                'not_member': {
                    'en': "⚠️ <b>The bot is not in this group</b>, so nothing is moderated there.\n\nTap the "
                          "button below and pick the group: Telegram will add the bot with the rights it needs. "
                          "Then the group works again and its page opens.",
                    'ru': "⚠️ <b>Бота нет в этой группе</b>, модерации там нет.\n\nНажмите кнопку ниже и "
                          "выберите группу: Telegram добавит бота с нужными правами. После этого группа снова "
                          "заработает и откроется."
                },
            },
        },
        'term': {
            'one': {'en': "{days} day", 'ru': "{days} день"},
            'few': {'en': "{days} days", 'ru': "{days} дня"},
            'many': {'en': "{days} days", 'ru': "{days} дней"},
            'forever': {'en': "for good", 'ru': "навсегда"},
        },
        # The owner's page of the way in
        'owner': {
            'title': {'en': "🚪 <b>Outsiders: {chat_name}</b>",
                      'ru': "🚪 <b>Посторонние: {chat_name}</b>"},
            'intro': {
                'en': "What happens when someone off the whitelist writes? The bot always deletes the message, "
                      "and then:\n\n"
                      "🔕 <b>Quietly</b> – nothing more.\n"
                      "🔔 <b>Tell me</b> – you get their message and an \"Allow\" button.\n"
                      "📨 <b>By request</b> – they get a link and ask for access; you approve in one tap.\n"
                      "💳 <b>Paid</b> – they pick a term and pay; you confirm the payment, or it confirms itself.",
                'ru': "Что делать, когда пишет тот, кого нет в белом списке? Сообщение бот удаляет всегда, а "
                      "дальше:\n\n"
                      "🔕 <b>Молча</b> – больше ничего.\n"
                      "🔔 <b>Сообщать мне</b> – вам приходит его сообщение и кнопка \"Разрешить\".\n"
                      "📨 <b>По заявке</b> – бот даёт ему ссылку, он просит доступ, вы одобряете в одно нажатие.\n"
                      "💳 <b>За плату</b> – он выбирает срок и платит, вы подтверждаете оплату, или она "
                      "подтверждается сама."
            },
            'mode': {
                'silent': {'en': "Now: 🔕 quietly", 'ru': "Сейчас: 🔕 молча"},
                'alert': {'en': "Now: 🔔 tell me", 'ru': "Сейчас: 🔔 сообщать мне"},
                'request': {
                    'en': "Now: 📨 by request, free. They ask for access on the group's page in the bot, "
                          "you approve.",
                    'ru': "Сейчас: 📨 по заявке, бесплатно. Человек просит доступ на странице группы в боте, "
                          "вы одобряете."},
                'paid': {
                    'en': "Now: 💳 paid. They pick a term on the group's page in the bot and pay.",
                    'ru': "Сейчас: 💳 за плату. Человек выбирает срок на странице группы в боте и платит."},
            },
            'prices': {'en': "Prices: {plans}", 'ru': "Цены: {plans}"},
            'prices_none': {'en': "Prices: not set", 'ru': "Цены: не заданы"},
            'payment': {'en': "Payment: {payment}\nYou check the payment and confirm the request.",
                        'ru': "Оплата: {payment}\nВы проверяете оплату и подтверждаете заявку."},
            'payment_none': {'en': "Payment: no way to pay set", 'ru': "Оплата: способ не задан"},
            'payment_provider': {
                'yoomoney': {
                    'en': "Payment: 🟣 YooMoney, the wallet {label}\nMembers pay by card, access opens by itself.",
                    'ru': "Оплата: 🟣 ЮMoney, кошелёк {label}\nУчастники платят картой, доступ открывается сам."
                },
                'tribute': {
                    'en': "Payment: 🎫 Tribute, a product per term\nThe webhook address for Tribute (Settings, API "
                          "Keys):\n<code>{url}</code>",
                    'ru': "Оплата: 🎫 Tribute, товар на каждый срок\nАдрес вебхука для Tribute (Настройки, API "
                          "Keys):\n<code>{url}</code>"
                },
                'cryptobot': {
                    'en': "Payment: 💎 CryptoBot, the app \"{label}\"\nAccess opens by itself once paid; the money "
                          "goes to your app.",
                    'ru': "Оплата: 💎 CryptoBot, приложение \"{label}\"\nДоступ открывается сам после оплаты, деньги "
                          "приходят в ваше приложение."
                },
            },
            'terms': {'en': "Terms:\n<blockquote>{terms}</blockquote>", 'ru': "Условия:\n<blockquote>{terms}</blockquote>"},
            'terms_none': {
                'en': "Terms: not set. Say what a member gets, the rules and how to reach you.",
                'ru': "Условия: не заданы. Напишите, что получает участник, правила и как с вами связаться."
            },
            'link': {
                'en': "The link for members:\n<code>{link}</code>\nThe bot adds it to its notice when it deletes "
                      "a message. While the way in is on, you get their requests, not an alert about every "
                      "stranger.",
                'ru': "Ссылка для участников:\n<code>{link}</code>\nБот сам добавляет её к сообщению тем, чьё "
                      "сообщение удалил. Пока вход включён, вам приходят их заявки, а не оповещение о каждом "
                      "постороннем."
            },
            'pending': {'en': "⏳ Waiting for your answer: {count}", 'ru': "⏳ Ждут ответа: {count}"},
            'paid_fallback': {
                'en': "⚠️ Paid entry works on a paid tariff; until then members see entry by request. "
                      "More: /subscription",
                'ru': "⚠️ Платный вход работает на платном тарифе, пока участники видят вход по заявке. "
                      "Подробнее: /subscription"
            },
            'paid_incomplete': {
                'en': "⚠️ Set prices and a way to pay to turn payment on. Until then members see entry by request.",
                'ru': "⚠️ Чтобы включить оплату, задайте цены и способ оплаты. Пока участники видят вход по заявке."
            },
            'everyone_note': {
                'en': "ℹ️ Everyone writes in the group now, so nobody needs a way in. It works again once you "
                      "turn the whitelist back on.",
                'ru': "ℹ️ Сейчас в группе пишут все, заявки не нужны. Они заработают, когда вы вернёте "
                      "белый список."
            },
            'step': {'en': "<b>Step {step} of 2</b>", 'ru': "<b>Шаг {step} из 2</b>"},
            'post_confirm': {
                'en': "📌 <b>The way in, in the group: {chat_name}</b>\n\nThe bot posts this message in the group and "
                      "pins it, so that everyone sees it:\n\n<blockquote>{text}\n[ {button} ]</blockquote>\n\nThe "
                      "button opens the group's page in the bot, where an outsider asks for access or pays for it. "
                      "Posted before? The bot deletes the old message.",
                'ru': "📌 <b>Вход прямо в группе: {chat_name}</b>\n\nБот опубликует в группе такое сообщение и "
                      "закрепит его, чтобы его видели все:\n\n<blockquote>{text}\n[ {button} ]</blockquote>\n\n"
                      "Кнопка ведёт на страницу группы в боте: там посторонний попросит доступ или оплатит его. "
                      "Если публиковали раньше, старое сообщение бот удалит."
            },
            'buttons': {
                'modes': {
                    'silent': {'en': "🔕 Quietly", 'ru': "🔕 Молча"},
                    'alert': {'en': "🔔 Tell me", 'ru': "🔔 Сообщать мне"},
                    'request': {'en': "📨 By request", 'ru': "📨 По заявке"},
                    'paid': {'en': "💳 Paid", 'ru': "💳 За плату"},
                },
                'current': {'en': "• ", 'ru': "• "},
                'locked': {'en': "🔒 ", 'ru': "🔒 "},
                'prices': {'en': "💰 Prices", 'ru': "💰 Цены"},
                'payment': {'en': "💳 Way to pay", 'ru': "💳 Способ оплаты"},
                'terms': {'en': "✏️ Terms", 'ru': "✏️ Условия"},
                'post': {'en': "📌 Button in the group", 'ru': "📌 Кнопка в группе"},
                'post_go': {'en': "📌 Post and pin", 'ru': "📌 Опубликовать и закрепить"},
                'requests': {'en': "📨 Requests ({count})", 'ru': "📨 Заявки ({count})"},
                'declined': {'en': "🚫 Declined ({count})", 'ru': "🚫 Отклонённые ({count})"},
                'cancel': {'en': "✖️ Cancel", 'ru': "✖️ Отмена"},
                'use_cryptobot': {'en': "💎 CryptoBot: access opens by itself",
                                  'ru': "💎 CryptoBot: доступ открывается сам"},
                'other_ways': {'en': "⬅️ Other ways", 'ru': "⬅️ Другие способы"},
                'use_yoomoney': {'en': "🟣 YooMoney: access opens by itself", 'ru': "🟣 ЮMoney: доступ открывается сам"},
                'use_tribute': {'en': "🎫 Tribute: access opens by itself", 'ru': "🎫 Tribute: доступ открывается сам"},
            },
            'prompt': {
                'prices': {
                    'en': "💰 Send the prices in one message, a line per term: the days, then the price.\n\n"
                          "For example:\n<pre>7 3$\n30 10$\nforever 30$</pre>That is 7 days for $3, 30 days "
                          "for $10 and access for good for $30.\n\nThe term in words works too: <code>week 3$</code>, "
                          "<code>month 10$</code>. Currency: ₽, $, €, USDT or TON, {currency} if none is named.",
                    'ru': "💰 Пришлите цены одним сообщением, по строке на срок: сначала дни, потом цена.\n\n"
                          "Например:\n<pre>7 300 ₽\n30 1000 ₽\nforever 3000 ₽</pre>Это 7 дней за 300 ₽, 30 дней "
                          "за 1000 ₽ и доступ навсегда за 3000 ₽.\n\nСрок можно писать и словами: <code>week 300 ₽"
                          "</code>, <code>month 1000 ₽</code>. Валюта: ₽, $, €, USDT или TON, без неё – {currency}."
                },
                'payment': {
                    'en': "💳 How will members pay? Pick one:\n\n🔗 <b>Your link or details</b>: just send them as "
                          "the next message, e.g. <code>https://boosty.to/you</code> or a card number. A member pays "
                          "and taps \"I paid\", you confirm in one tap.\n\n⚡ <b>Or connect a service</b> with a "
                          "button below, and access opens by itself once paid:\n💎 CryptoBot: crypto\n"
                          "🟣 YooMoney: cards, rubles only\n🎫 Tribute: cards, a product per term",
                    'ru': "💳 Как участники будут платить? Выберите одно:\n\n🔗 <b>Своя ссылка или реквизиты</b>: "
                          "просто пришлите их следующим сообщением, например <code>https://boosty.to/you</code> или "
                          "номер карты. Участник оплатит и нажмёт \"Я оплатил(а)\", вы подтвердите в одно "
                          "нажатие.\n\n⚡ <b>Или подключите сервис</b> кнопкой ниже, и доступ откроется сам после "
                          "оплаты:\n💎 CryptoBot: криптовалюта\n🟣 ЮMoney: карты, только рубли\n"
                          "🎫 Tribute: карты, товар на каждый срок"
                },
                'yoomoney_wallet': {
                    'en': "🟣 <b>Connecting YooMoney</b>\n\nSend the number of your YooMoney wallet: 15 to 20 "
                          "digits starting with 41, shown in the wallet under the balance.",
                    'ru': "🟣 <b>Подключение ЮMoney</b>\n\nПришлите номер кошелька ЮMoney: от 15 до 20 цифр, "
                          "начинается с 41, виден в кошельке под балансом."
                },
                'yoomoney_secret': {
                    'en': "🟣 <b>Connecting YooMoney</b>, the wallet {wallet}\n\n1. Open <a href=\"{settings}\">"
                          "HTTP notifications</a> in YooMoney.\n2. Paste this address:\n<code>{url}</code>\n"
                          "3. Turn on \"Send HTTP notifications\", tap \"Show the secret\" and send the secret "
                          "here. The bot deletes the message with it.\n4. Save, then tap \"Test\": the bot will "
                          "confirm.\n\nMembers pay by card; YooMoney keeps 3% of what you receive.",
                    'ru': "🟣 <b>Подключение ЮMoney</b>, кошелёк {wallet}\n\n1. Откройте в ЮMoney <a href=\"{settings}\">"
                          "HTTP-уведомления</a>.\n2. Вставьте адрес:\n<code>{url}</code>\n3. Включите \"Отправлять "
                          "HTTP-уведомления\", нажмите \"Показать секрет\" и пришлите секрет сюда. Бот удалит "
                          "сообщение с ним.\n4. Сохраните и нажмите \"Протестировать\": бот пришлёт подтверждение.\n\n"
                          "Участники платят картой, ЮMoney удерживает 3% с получателя."
                },
                'tribute_key': {
                    'en': "🎫 <b>Connecting Tribute</b>\n\n1. Make a digital product in Tribute for each term: "
                          "{plans}.\n2. In Tribute open ⋯ → Settings → API Keys, make a key and send it here. The "
                          "bot deletes the message with it.",
                    'ru': "🎫 <b>Подключение Tribute</b>\n\n1. Создайте в Tribute цифровой товар на каждый срок: "
                          "{plans}.\n2. Откройте в Tribute ⋯ → Настройки → API Keys, создайте ключ и пришлите его "
                          "сюда. Бот удалит сообщение с ним."
                },
                'tribute_map': {
                    'en': "🎫 Which of your Tribute products gives access for <b>{plan}</b>?",
                    'ru': "🎫 Какой товар Tribute даёт доступ на <b>{plan}</b>?"
                },
                'cryptobot': {
                    'en': "💎 <b>Connecting CryptoBot</b>\n\n1. Open @CryptoBot → Crypto Pay → Create App.\n"
                          "2. In the app, open API Token and send the token here.\n\nThe money goes to your app in "
                          "@CryptoBot; the bot only makes invoices and checks them. The token is kept encrypted and "
                          "the bot deletes the message with it at once. Prices in ₽, $ and € are paid in any coin, "
                          "prices in USDT and TON in that coin.",
                    'ru': "💎 <b>Подключение CryptoBot</b>\n\n1. Откройте @CryptoBot → Crypto Pay → Create App.\n"
                          "2. В приложении откройте API Token и пришлите токен сюда.\n\nДеньги приходят в ваше "
                          "приложение в @CryptoBot, бот только выставляет счета и проверяет оплату. Токен хранится "
                          "зашифрованным, а сообщение с ним бот сразу удалит. Цены в ₽, $ и € участник оплатит "
                          "любой монетой, цены в USDT и TON – этой монетой."
                },
                'terms': {
                    'en': "✏️ Send the terms in one message, up to 1000 characters: what a member gets, the rules, "
                          "how to reach you.\n\nTo remove them, send <code>-</code>.",
                    'ru': "✏️ Пришлите условия одним сообщением, до 1000 знаков: что получает участник, правила, "
                          "как с вами связаться.\n\nЧтобы убрать условия, пришлите <code>-</code>."
                },
            },
            'errors': {
                'prices_bad': {
                    'en': "Could not read:\n{lines}\n\nWrite the term and the price, e.g. <code>30 10</code>.",
                    'ru': "Не понял строки:\n{lines}\n\nПишите срок и цену, например <code>30 1000</code>."
                },
                'too_long': {'en': "Too long: {length} characters, up to {max} fit.",
                             'ru': "Слишком длинно: {length} знаков, можно до {max}."},
                'paid_only': {'en': "Paid entry is on paid tariffs. More: /subscription",
                              'ru': "Платный вход есть на платных тарифах. Подробнее: /subscription"},
                'not_editing': {'en': "Pick what to change with the buttons below.",
                                'ru': "Выберите кнопкой ниже, что изменить."},
                'yoomoney_wallet': {'en': "❌ That is not a YooMoney wallet number: 15 to 20 digits starting with 41.",
                                    'ru': "❌ Это не номер кошелька ЮMoney: от 15 до 20 цифр, начинается с 41."},
                'yoomoney_secret': {'en': "❌ That does not look like the secret: copy it whole, without spaces.",
                                    'ru': "❌ Не похоже на секрет: скопируйте его целиком, без пробелов."},
                'tribute_key': {'en': "❌ Tribute did not take the key. Check it and send it again.",
                                'ru': "❌ Tribute не принял ключ. Проверьте его и пришлите ещё раз."},
                'tribute_no_products': {
                    'en': "❌ There are no digital products in your Tribute. Make one per term and send the key again.",
                    'ru': "❌ В вашем Tribute нет цифровых товаров. Создайте по товару на срок и пришлите ключ снова."
                },
                'pick_product': {'en': "Pick a product with the buttons below.", 'ru': "Выберите товар кнопкой ниже."},
                'cryptobot_token': {
                    'en': "❌ CryptoBot did not take the token. Check that you copied all of it and send it again.",
                    'ru': "❌ CryptoBot не принял токен. Проверьте, что скопировали его целиком, и пришлите ещё раз."
                },
            },
            'toasts': {
                'saved': {'en': "Saved", 'ru': "Сохранено"},
                'request_on': {'en': "Outsiders can ask for access now", 'ru': "Теперь посторонние могут попросить доступ"},
                'paid_on': {'en': "Outsiders can pay for access now", 'ru': "Теперь посторонние могут оплатить доступ"},
                'silent_on': {'en': "Off-list messages go quietly", 'ru': "Чужие сообщения удаляются молча"},
                'alert_on': {'en': "You will be told when someone off the list writes",
                             'ru': "Будем сообщать, когда пишет кто-то не из списка"},
                'posted': {'en': "Posted in the group and pinned", 'ru': "Отправлено в группу и закреплено"},
                'posted_unpinned': {'en': "Posted in the group. Pin it so that everyone sees it.",
                                    'ru': "Отправлено в группу. Закрепите сообщение, чтобы его видели все."},
                'post_failed': {'en': "Could not post in the group: the bot may not send messages there.",
                                'ru': "Не получилось отправить в группу: у бота нет права писать сообщения."},
                'no_requests': {'en': "No requests waiting", 'ru': "Новых заявок нет"},
                'requests_sent': {'en': "The requests are below", 'ru': "Заявки ниже"},
                'no_declined': {'en': "Nobody declined in the last 7 days", 'ru': "За 7 дней никого не отклоняли"},
                'declined_sent': {'en': "Declined in the last 7 days are below. Undo lets them ask again and unmutes "
                                        "them", 'ru': "Отклонённые за 7 дней ниже. \"Отменить\" вернёт заявку и снимет мут"},
                'yoomoney_connected': {
                    'en': "✅ YooMoney is connected. Tap \"Test\" on its notifications page: the bot will confirm.",
                    'ru': "✅ ЮMoney подключён. Нажмите \"Протестировать\" на странице уведомлений: бот подтвердит."
                },
                'yoomoney_rubles': {
                    'en': "✅ YooMoney is connected. It takes rubles only: set the prices in ₽.",
                    'ru': "✅ ЮMoney подключён. Он принимает только рубли: укажите цены в ₽."
                },
                'tribute_connected': {
                    'en': "✅ Tribute is connected. The last step: in Tribute → Settings → API Keys put this as the "
                          "Webhook URL and save:\n<code>{url}</code>",
                    'ru': "✅ Tribute подключён. Последний шаг: в Tribute → Настройки → API Keys вставьте в Webhook URL "
                          "и сохраните:\n<code>{url}</code>"
                },
                'cryptobot_connected': {
                    'en': "✅ CryptoBot is connected: the app \"{label}\". The message with the token is deleted.",
                    'ru': "✅ CryptoBot подключён: приложение \"{label}\". Сообщение с токеном удалено."
                },
            },
        },
        # Plain text: the message posted in the group, and the line added to the notice about a deleted message
        'group_post': {
            'text': {'en': "✍️ Only members on the list write in this group. To get access, tap the button.",
                     'ru': "✍️ Писать в группе могут участники из списка. Чтобы получить доступ, нажмите кнопку."},
            'button': {'en': "🔑 Get access", 'ru': "🔑 Получить доступ"},
        },
        'providers': {
            'cryptobot': {'en': "CryptoBot", 'ru': "CryptoBot"},
            'yoomoney': {'en': "YooMoney", 'ru': "ЮMoney"},
            'tribute': {'en': "Tribute", 'ru': "Tribute"},
        },
        'providers_member': {
            'cryptobot': {'en': "@CryptoBot", 'ru': "@CryptoBot"},
            'yoomoney': {'en': "YooMoney (by card)", 'ru': "ЮMoney (картой)"},
            'tribute': {'en': "Tribute", 'ru': "Tribute"},
        },
        # The managers hear what YooMoney and Tribute told the bot
        'hooks': {
            'yoomoney_test': {
                'en': "✅ YooMoney reaches the bot: payments for <b>{chat_name}</b> will open access by themselves.",
                'ru': "✅ ЮMoney достучался до бота: оплаты за <b>{chat_name}</b> будут открывать доступ сами."
            },
            'yoomoney_short': {
                'en': "⚠️ {member} paid {paid} for <b>{chat_name}</b>, the price is {price}. Access is not opened: "
                      "decide yourself.",
                'ru': "⚠️ {member} заплатил(а) {paid} за <b>{chat_name}</b>, а цена {price}. Доступ не открыт: "
                      "решите сами."
            },
            'tribute_no_buyer': {
                'en': "⚠️ Tribute sold \"{product}\" for <b>{chat_name}</b> without the buyer's Telegram account, so "
                      "access is not opened. Let them in yourself.",
                'ru': "⚠️ Tribute продал \"{product}\" для <b>{chat_name}</b> без аккаунта Telegram покупателя, "
                      "поэтому доступ не открыт. Пустите его сами."
            },
            'tribute_refund': {
                'en': "↩️ Tribute refunded the payment of {member} for <b>{chat_name}</b>. Take the access away?",
                'ru': "↩️ Tribute вернул оплату {member} за <b>{chat_name}</b>. Убрать доступ?"
            },
            'remove_access': {'en': "🚫 Take the access away", 'ru': "🚫 Убрать доступ"},
        },
        'notice': {
            'en': "Your message is deleted: only members on the list write in this group.\n\nGet access: {link}",
            'ru': "Ваше сообщение удалено: писать в этой группе могут только участники из списка.\n\n"
                  "Получить доступ: {link}"
        },
        # The member's page of the group
        # /access: the member's groups, HTML
        'mine': {
            'title': {'en': "🔑 <b>Where you can write</b>\n", 'ru': "🔑 <b>Где вы можете писать</b>\n"},
            'until': {'en': "✅ {chat_name}: until {date}", 'ru': "✅ {chat_name}: до {date}"},
            'forever': {'en': "✅ {chat_name}: for good", 'ru': "✅ {chat_name}: бессрочно"},
            'waiting': {'en': "⏳ {chat_name}: your request of {date} is waiting for the owner",
                        'ru': "⏳ {chat_name}: заявка от {date} ждёт ответа владельца"},
            'empty': {
                'en': "🔑 No access through the bot yet. A group's owner gives the link to get in; the bot also "
                      "sends it when it deletes a message of someone off the list.",
                'ru': "🔑 Доступов через бота пока нет. Ссылку на вход даёт владелец группы, а ещё бот присылает "
                      "её, когда удаляет сообщение того, кого нет в списке."
            },
            'buttons': {
                'extend': {'en': "⏳ Extend: {chat_name}", 'ru': "⏳ Продлить: {chat_name}"},
                'open': {'en': "{chat_name}", 'ru': "{chat_name}"},
            },
        },
        'member': {
            'admin': {
                'en': "👮 You are an admin of <b>{chat_name}</b>, so you write without access. Members off the "
                      "whitelist see here a way to ask for it or pay.\n\nTo try it yourself, turn on "
                      "\"👮 Admins: checked too\" on the group's page.",
                'ru': "👮 Вы администратор <b>{chat_name}</b> и пишете без доступа. Те, кого нет в белом списке, "
                      "видят здесь, как попросить доступ или оплатить его.\n\nЧтобы попробовать самому, включите "
                      "\"👮 Админы: тоже проверять\" на странице группы."
            },
            'title': {'en': "✍️ <b>{chat_name}</b>", 'ru': "✍️ <b>{chat_name}</b>"},
            'intro': {'en': "Only members on the list write in this group.",
                      'ru': "Писать в этой группе могут только участники из списка."},
            'request_hint': {'en': "Tap the button and the group's owner gets your request.",
                             'ru': "Нажмите кнопку, и владелец группы получит заявку."},
            'paid_hint': {'en': "Pick a term:", 'ru': "Выберите срок:"},
            'have_forever': {'en': "✅ You have access to this group, you can write.",
                             'ru': "✅ У вас есть доступ к этой группе, можно писать."},
            'have_until': {'en': "✅ You have access until {date}.", 'ru': "✅ У вас есть доступ до {date}."},
            'extend_hint': {'en': "To extend it now, pick a term: the days are added to the current ones.",
                            'ru': "Продлить заранее: выберите срок, дни добавятся к текущим."},
            'pending': {'en': "⏳ Request sent on {date}. Waiting for the group's owner.",
                        'ru': "⏳ Заявка отправлена {date}. Ждём ответа владельца группы."},
            'pending_paid': {'en': "⏳ Payment reported on {date}: {plan}. The owner checks it and lets you in.",
                             'ru': "⏳ Об оплате сообщили {date}: {plan}. Владелец проверит её и откроет доступ."},
            'rejected_recently': {
                'en': "The owner declined your request on {date}. You can ask again in a few hours.",
                'ru': "Владелец отклонил заявку {date}. Попробовать снова можно через несколько часов."
            },
            'off': {'en': "The owner of this group does not take requests through the bot yet.",
                    'ru': "Владелец этой группы пока не принимает заявки через бота."},
            'not_found': {'en': "The group is not found. The link may be old.",
                          'ru': "Группа не найдена. Возможно, ссылка устарела."},
            'footer': {
                'en': "<i>This is @{bot}: it lets into a group only those its owner allows. All your access: "
                      "/access. Your own group: /start</i>",
                'ru': "<i>Это @{bot}: он пускает в группу только тех, кого разрешил владелец. Все ваши доступы: "
                      "/access. Своя группа: /start</i>"
            },
            'plan': {
                'en': "💳 <b>{chat_name}</b>: {plan}\n\n1. Pay the group's owner by the link below.\n"
                      "2. Come back and tap \"I paid\": the owner checks the payment and lets you in.",
                'ru': "💳 <b>{chat_name}</b>: {plan}\n\n1. Оплатите владельцу группы по ссылке ниже.\n"
                      "2. Вернитесь и нажмите \"Я оплатил(а)\": владелец проверит оплату и откроет доступ."
            },
            'plan_details': {
                'en': "💳 <b>{chat_name}</b>: {plan}\n\n1. Pay the group's owner:\n<blockquote>{payment}</blockquote>\n"
                      "2. Come back and tap \"I paid\": the owner checks the payment and lets you in.",
                'ru': "💳 <b>{chat_name}</b>: {plan}\n\n1. Оплатите владельцу группы:\n<blockquote>{payment}</blockquote>\n"
                      "2. Вернитесь и нажмите \"Я оплатил(а)\": владелец проверит оплату и откроет доступ."
            },
            'plan_auto': {
                'en': "💳 <b>{chat_name}</b>: {plan}\n\nPay through {provider} with the button below. Access opens "
                      "by itself, usually within a minute of paying.",
                'ru': "💳 <b>{chat_name}</b>: {plan}\n\nОплатите через {provider} по кнопке ниже. Доступ откроется "
                      "сам, обычно в течение минуты после оплаты."
            },
            'plan_tribute': {
                'en': "💳 <b>{chat_name}</b>: {plan}\n\nPay in Tribute with the button below, from this Telegram "
                      "account. Access opens by itself, usually within a minute of paying.",
                'ru': "💳 <b>{chat_name}</b>: {plan}\n\nОплатите в Tribute по кнопке ниже, с этого же аккаунта "
                      "Telegram. Доступ откроется сам, обычно в течение минуты после оплаты."
            },
            'plan_auto_note': {
                'en': "<i>The money goes to the group's owner; the bot only checks the payment.</i>",
                'ru': "<i>Деньги идут владельцу группы, бот только проверяет оплату.</i>"
            },
            'pending_auto': {'en': "⏳ An invoice to pay: {plan}. Access opens by itself once you pay.",
                             'ru': "⏳ Счёт на оплату: {plan}. После оплаты доступ откроется сам."},
            'paid_until': {'en': "✅ Payment received. You may write in <b>{chat_name}</b> until {date}.",
                           'ru': "✅ Оплата получена. Доступ к группе <b>{chat_name}</b> открыт до {date}. Можно писать."},
            'paid_forever': {'en': "✅ Payment received. You may write in <b>{chat_name}</b> for good.",
                             'ru': "✅ Оплата получена. Доступ к группе <b>{chat_name}</b> открыт навсегда. Можно писать."},
            'plan_note': {
                'en': "<i>The bot does not take or check payments: the money goes to the group's owner.</i>",
                'ru': "<i>Бот не принимает и не проверяет платежи: деньги идут владельцу группы.</i>"
            },
            'buttons': {
                'settings': {'en': "⚙️ The group's page", 'ru': "⚙️ Страница группы"},
                'request': {'en': "📨 Ask for access", 'ru': "📨 Попросить доступ"},
                'remind': {'en': "🔔 Remind the owner", 'ru': "🔔 Напомнить владельцу"},
                'cancel_request': {'en': "✖️ Cancel the request", 'ru': "✖️ Отменить заявку"},
                'pay': {'en': "💳 Pay {amount}", 'ru': "💳 Оплатить {amount}"},
                'paid': {'en': "✅ I paid", 'ru': "✅ Я оплатил(а)"},
                'back': {'en': "⬅️ Back", 'ru': "⬅️ Назад"},
                'renew': {'en': "🔄 Extend", 'ru': "🔄 Продлить"},
                'ask_again': {'en': "📨 Ask again", 'ru': "📨 Попросить снова"},
                'open_group': {'en': "💬 Open the group", 'ru': "💬 Открыть группу"},
                'check': {'en': "🔄 Check the payment", 'ru': "🔄 Проверить оплату"},
                'other_term': {'en': "⬅️ Another term", 'ru': "⬅️ Другой срок"},
            },
            'toasts': {
                'sent': {'en': "Request sent", 'ru': "Заявка отправлена"},
                'already': {'en': "Your request is already with the owner", 'ru': "Заявка уже у владельца"},
                'reminded': {'en': "The owner is reminded", 'ru': "Напомнили владельцу"},
                'cancelled': {'en': "The request is cancelled", 'ru': "Заявка отменена"},
                'too_soon': {'en': "You can remind in a few hours", 'ru': "Напомнить можно через несколько часов"},
                'unavailable': {'en': "This option is no longer offered", 'ru': "Этот вариант больше не предлагается"},
                'not_paid_yet': {'en': "No payment yet. If you have paid, give it a minute.",
                                 'ru': "Оплата пока не пришла. Если вы уже оплатили, подождите минуту."},
                'provider_error': {'en': "The payment service did not answer. Try again in a minute.",
                                   'ru': "Платёжная система не ответила. Попробуйте через минуту."},
            },
            # Sent to the member when the owner decides, and about the end of a term
            'approved_forever': {'en': "✅ The owner let you into <b>{chat_name}</b>. You can write.",
                                 'ru': "✅ Владелец открыл вам доступ к группе <b>{chat_name}</b>. Можно писать."},
            'approved_until': {
                'en': "✅ The owner let you into <b>{chat_name}</b> until {date}. You can write.",
                'ru': "✅ Владелец открыл вам доступ к группе <b>{chat_name}</b> до {date}. Можно писать."
            },
            'rejected': {'en': "The owner of <b>{chat_name}</b> declined your request.",
                         'ru': "Владелец группы <b>{chat_name}</b> отклонил заявку."},
            'rejected_paid': {
                'en': "The owner of <b>{chat_name}</b> did not confirm your payment. If you paid, contact them: "
                      "groups usually give contacts in their terms.",
                'ru': "Владелец группы <b>{chat_name}</b> не подтвердил оплату. Если вы оплатили, свяжитесь с ним: "
                      "контакты обычно есть в условиях группы."
            },
            'expiry_soon': {'en': "⏳ Your access to <b>{chat_name}</b> ends on {date}.",
                            'ru': "⏳ Доступ к группе <b>{chat_name}</b> заканчивается {date}."},
            'expiry_ended': {'en': "Your access to <b>{chat_name}</b> has ended.",
                             'ru': "Доступ к группе <b>{chat_name}</b> закончился."},
        },
        # The managers' side of a request
        'alert': {
            'request': {'en': "📨 <b>Access request</b> to <b>{chat_name}</b>\n{member}",
                        'ru': "📨 <b>Заявка на доступ</b> к группе <b>{chat_name}</b>\n{member}"},
            'paid': {
                'en': "💳 <b>Payment for access</b> to <b>{chat_name}</b>\n{member} says they paid: {plan}.\n"
                      "Check that the money came and confirm.",
                'ru': "💳 <b>Оплата доступа</b> к группе <b>{chat_name}</b>\n{member} сообщает об оплате: {plan}.\n"
                      "Проверьте поступление и подтвердите."
            },
            'reminder': {'en': "🔔 The member reminds you of the request.", 'ru': "🔔 Участник напоминает о заявке."},
            'buttons': {
                'confirm': {'en': "✅ Confirm: {term}", 'ru': "✅ Подтвердить: {term}"},
                'forever': {'en': "✅ For good", 'ru': "✅ Навсегда"},
                'days': {'en': "✅ {days} days", 'ru': "✅ {days} дней"},
                'reject': {'en': "❌ Decline", 'ru': "❌ Отклонить"},
                'undo_refund': {'en': "💸 Take away, cancel the payment", 'ru': "💸 Убрать, оплату отменить"},
                'undo_keep': {'en': "↩️ Take away, the payment stays", 'ru': "↩️ Убрать, оплата остаётся"},
                'undo_no': {'en': "✅ Keep the access", 'ru': "✅ Оставить доступ"},
            },
            'approved_forever': {'en': "✅ {member} may write in <b>{chat_name}</b> for good.",
                                 'ru': "✅ {member}: доступ к <b>{chat_name}</b> открыт навсегда."},
            'approved_until': {'en': "✅ {member} may write in <b>{chat_name}</b> until {date}.",
                               'ru': "✅ {member}: доступ к <b>{chat_name}</b> открыт до {date}."},
            'rejected': {'en': "❌ The request of {member} to <b>{chat_name}</b> is declined.",
                         'ru': "❌ Заявка {member} в <b>{chat_name}</b> отклонена."},
            'decided': {'en': "This request has been answered already.", 'ru': "На эту заявку уже ответили."},
            'paid_auto': {'en': "💰 <b>Paid through {provider}</b>: {member}, {plan}, the group <b>{chat_name}</b>.",
                          'ru': "💰 <b>Оплата через {provider}</b>: {member}, {plan}, группа <b>{chat_name}</b>."},
            'paid_auto_until': {'en': "Access is open until {date}.", 'ru': "Доступ открыт до {date}."},
            'paid_auto_forever': {'en': "Access is open for good.", 'ru': "Доступ открыт навсегда."},
            'approved_toast': {'en': "Access given", 'ru': "Доступ открыт"},
            'rejected_toast': {'en': "Declined", 'ru': "Отклонено"},
            'undo_paid': {
                'en': "Take the access of {member} to <b>{chat_name}</b> away? They paid: {plan}.",
                'ru': "Убрать доступ {member} к <b>{chat_name}</b>? Оплата была: {plan}."
            },
            'refunded': {'en': "💸 The payment is cancelled and no longer counted. Return the money yourself.",
                         'ru': "💸 Оплата отменена и больше не считается. Деньги верните сами."},
            'payment_kept': {'en': "💰 The payment stays counted.", 'ru': "💰 Оплата остаётся в статистике."},
            'kept': {'en': "✅ {member} keeps the access to <b>{chat_name}</b>.",
                     'ru': "✅ Доступ {member} к <b>{chat_name}</b> остаётся."},
            'reopened_toast': {'en': "The request is waiting for your answer again",
                               'ru': "Заявка снова ждёт ответа"},
        },
    },
    # /usersCount (also /stats) for a group owner, HTML
    'stats': {
        'no_groups': {
            'en': "📊 No groups yet, so nothing to count. Connect the first one: /add_chat",
            'ru': "📊 Групп пока нет, считать нечего. Подключите первую: /add_chat"
        },
        'title': {
            'en': "📊 <b>Your groups: {count}</b> (moderated {on}, off or paused {off})",
            'ru': "📊 <b>Ваши группы: {count}</b> (модерируются {on}, на паузе или отключены {off})"
        },
        'members': {
            'en': "👥 Members in all: {count}",
            'ru': "👥 Участников всего: {count}"
        },
        'whitelist': {
            'en': "✅ On whitelists: {count} (for a term: {timed})",
            'ru': "✅ В белых списках: {count} (на срок: {timed})"
        },
        'removed': {
            'en': "🗑 Deleted: today {day}, 7 days {week}, 30 days {month}",
            'ru': "🗑 Удалено: сегодня {day}, за 7 дней {week}, за 30 дней {month}"
        },
        'group_members': {
            'en': "👥 {count} members",
            'ru': "👥 Участников: {count}"
        },
        'group_whitelist': {
            'en': "✅ whitelist {count} (for a term: {timed})",
            'ru': "✅ в списке {count} (на срок: {timed})"
        },
        'payments': {
            'en': "💰 Paid entries in 30 days: {count}, {amount}",
            'ru': "💰 Оплат за вход за 30 дней: {count}, на {amount}"
        },
        'more': {
            'en': "…and {count} more groups, counted above",
            'ru': "…и ещё групп: {count}, они учтены в сумме выше"
        },
    },
    # The command menus (setMyCommands): up to 256 characters each, plain text
    'commands': {
        'private': {
            'menu': {'en': "Main menu", 'ru': "Главное меню"},
            'my_chats': {'en': "My groups", 'ru': "Мои группы"},
            'stats': {'en': "Members and statistics of my groups", 'ru': "Участники и статистика моих групп"},
            'access': {'en': "Groups where I can write", 'ru': "Группы, где я могу писать"},
            'add_chat': {'en': "Connect a group", 'ru': "Подключить группу"},
            'subscription': {'en': "Tariff and payment", 'ru': "Тариф и оплата"},
            'settings': {'en': "Settings", 'ru': "Настройки"},
            'help': {'en': "How it works", 'ru': "Как это работает"},
        },
        'group': {
            'allow': {'en': "Allow a member (in reply or @nick, 7d for a week)",
                      'ru': "Разрешить участнику (ответом или @nick, 7d на неделю)"},
            'deny': {'en': "Remove a member from the whitelist", 'ru': "Убрать участника из белого списка"},
            'settings': {'en': "The group's page in the bot", 'ru': "Страница группы в боте"},
        },
    },
    'tariffs': {
        # HTML, under the list of tariffs
        'features': {
            'en':
                "<b>Every tariff</b>: a whitelist, alerts with \"Allow\" in one tap, commands in the group, "
                "requests for access through the bot.\n"
                "<b>Paid tariffs</b> add access for 7 or 30 days, posting limits (1 a day, 3 an hour, 10 in 2 days…) and paid "
                "entry: newcomers pay you for a term.",
            'ru':
                "<b>На любом тарифе</b>: белый список, оповещения с \"Разрешить\" в одно нажатие, команды в группе, "
                "заявки на доступ через бота.\n"
                "<b>Платные тарифы</b> добавляют доступ на 7 или 30 дней, лимит постов (1 в день, 3 в час, 10 за 2 дня…) и "
                "платный вход: новые платят вам за срок."
        },
    },
}


def merge(target: dict, source: dict) -> dict:
    """Puts `source` into `target` key by key, its leaves replacing the target's."""
    for key, value in source.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict) and not ({'en', 'ru'} & set(value)):
            merge(target[key], value)
        else:
            target[key] = value
    return target
