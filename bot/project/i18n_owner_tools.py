"""Texts of the owner tools: the group page, timed access, posting limits, alerts to the group's managers,
commands in the group, and the onboarding that leads to them. Merged into routed_messages by project.i18n.

Keys are lower case (get_message lowers the route). Which texts are HTML is said next to them."""
from project import constants

_bot = constants.bot_nickname
ADD_TO_GROUP_URL = f"https://t.me/{_bot}?startgroup=connect&admin=delete_messages+restrict_members"

owner_tools_messages = {
    'welcome': {
        'introduction': {
            'en':
                "Hi! I keep your group clean: only the people you allow can write in it, everyone else's "
                "messages are deleted at once.\n\n"
                "Made for groups of ads and announcements, where the right to post is worth something:\n"
                "● a whitelist by nickname, id or a forwarded message\n"
                "● access for 7 or 30 days, ending on its own\n"
                "● a posting limit: 1 ad a day, 3 a week and so on\n"
                "● a message when a stranger writes, with \"Allow\" in one tap\n\n"
                "One group is free.",
            'ru':
                "Привет! Я слежу за порядком в группе: писать в ней могут только те, кого вы разрешили, "
                "остальные сообщения сразу удаляются.\n\n"
                "Сделан для групп объявлений и рекламы, где право писать чего-то стоит:\n"
                "● белый список по нику, id или пересланному сообщению\n"
                "● доступ на 7 или 30 дней, который сам заканчивается\n"
                "● лимит постов: 1 объявление в день, 3 в неделю и так далее\n"
                "● сообщение, когда пишет посторонний, и \"Разрешить\" в одно нажатие\n\n"
                "Одна группа бесплатно."
        },
    },
    'help': {
        'text': {
            'en':
                f"@{_bot} lets only the people you allow write in your group.\n\n"
                "<b>Connect a group</b>: /add_chat, then \"Add to a group\" and pick it. The bot needs to be "
                "an admin that can delete messages (and restrict members, for the pause after a deleted message).\n\n"
                "<b>Manage it</b>: /my_chats. On the group's page: the whitelist, who may write (the whitelist or "
                "everyone), the posting limit, alerts, pause.\n\n"
                "<b>Right in the group</b> (admins only, nobody else sees the answers):\n"
                "/allow in reply to a message, or /allow @nick 7d – let a member write (for 7 days)\n"
                "/deny @nick – take them off the list\n"
                "/settings – open the group's page here\n\n"
                "<b>Free</b>: one group with a whitelist and alerts. <b>Paid</b> (/subscription): more groups, "
                "access for a term and posting limits.\n\n"
                "Questions and ideas: @ascendit_chat",
            'ru':
                f"@{_bot} разрешает писать в группе только тем, кого вы допустили.\n\n"
                "<b>Подключить группу</b>: /add_chat, затем \"Добавить в группу\" и выберите её. Бот должен быть "
                "администратором с правом удалять сообщения (и ограничивать участников – для паузы после удаления).\n\n"
                "<b>Управлять</b>: /my_chats. На странице группы: белый список, кто пишет (белый список или все), "
                "лимит постов, оповещения, пауза.\n\n"
                "<b>Прямо в группе</b> (только админам, ответы видите только вы):\n"
                "/allow в ответ на сообщение или /allow @ник 7d – разрешить писать (на 7 дней)\n"
                "/deny @ник – убрать из списка\n"
                "/settings – открыть страницу группы здесь\n\n"
                "<b>Бесплатно</b>: одна группа с белым списком и оповещениями. <b>Платно</b> (/subscription): "
                "больше групп, доступ на срок и лимиты постов.\n\n"
                "Вопросы и идеи: @ascendit_chat"
        },
    },
    'add_chat': {
        # HTML
        'instruction': {
            'en':
                "<b>Connect a group</b>\n\n"
                "1. Tap \"Add to a group\" below and pick your group. Telegram will offer to make the bot an "
                "admin with the rights it needs – agree.\n"
                "2. That's it: the bot connects the group and sends you its page.\n\n"
                "Already added the bot as an admin? Tap \"Select a group\" at the bottom of the screen, or forward "
                "here a message written in the group on behalf of the group (anonymous admin).",
            'ru':
                "<b>Подключить группу</b>\n\n"
                "1. Нажмите \"Добавить в группу\" ниже и выберите вашу группу. Telegram предложит сделать бота "
                "администратором с нужными правами – согласитесь.\n"
                "2. Готово: бот подключит группу и пришлёт её страницу.\n\n"
                "Бот уже администратор? Нажмите \"Выбрать группу\" внизу экрана или перешлите сюда сообщение, "
                "написанное в группе от имени группы (анонимный администратор)."
        },
        'add_to_group_button': {
            'en': "➕ Add to a group",
            'ru': "➕ Добавить в группу"
        },
        'add_chat_reply_button_text': {
            'en': "Or pick a group where the bot is already an admin:",
            'ru': "Или выберите группу, где бот уже администратор:"
        },
        'add_chat_reply_button': {
            'en': "✅ Select a group",
            'ru': "✅ Выбрать группу"
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
    'access': {
        'chat': {
            'errors': {
                'not_registered': {
                    'en': "you have not started the bot yet",
                    'ru': "вы ещё не запускали бота"
                },
            }
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
            },
            'limit': {
                'off': {
                    'en': "no limit",
                    'ru': "без лимита"
                },
                'day': {
                    'en': "{limit} a day",
                    'ru': "{limit} в день"
                },
                'week': {
                    'en': "{limit} a week",
                    'ru': "{limit} в неделю"
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
                'en': "Limit: {limit}",
                'ru': "Лимит: {limit}"
            },
            'restriction_duration_button': {
                'en': "Pause: {duration} min",
                'ru': "Пауза: {duration} мин"
            },
            'alerts_button': {
                'on': {
                    'en': "🔔 Alerts",
                    'ru': "🔔 Оповещения"
                },
                'off': {
                    'en': "🔕 Alerts",
                    'ru': "🔕 Оповещения"
                },
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
            'alerts_toast': {
                'on': {
                    'en': "You will be told when someone off the list writes",
                    'ru': "Будем сообщать, когда пишет кто-то не из списка"
                },
                'off': {
                    'en': "Alerts are off for this group",
                    'ru': "Оповещения по этой группе выключены"
                },
            },
        },
        'add_to_whitelist': {
            # HTML
            'text': {
                'en':
                    "<b>Who may write?</b>\n\n"
                    "Send nicknames, ids or t.me links, separated by spaces: <code>@anna 123456789</code>\n"
                    "Or forward a message from the member, or pick them from your contacts with the button below.\n\n"
                    "Adding a term is possible: <code>@anna 7d</code>",
                'ru':
                    "<b>Кому разрешить писать?</b>\n\n"
                    "Пришлите ники, id или ссылки t.me через пробел: <code>@anna 123456789</code>\n"
                    "Или перешлите сообщение участника, или выберите его из контактов кнопкой ниже.\n\n"
                    "Можно указать срок: <code>@anna 7d</code>"
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
                'en': "Not understood: {words}. Send a nickname, an id or a t.me link",
                'ru': "Не понял: {words}. Пришлите ник, id или ссылку t.me"
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
            },
            'term_toast': {
                'forever': {
                    'en': "Access for good",
                    'ru': "Доступ бессрочный"
                },
                'days': {
                    'en': "Access for {days} days from now",
                    'ru': "Доступ на {days} дней с сегодняшнего дня"
                },
            },
        },
    },
    'work': {
        # Plain text, ephemeral: only the member sees it
        'limit_notice': {
            'day': {
                'en': "Your message was removed: members post up to {limit} a day here. Next one after {next_at}.",
                'ru': "Сообщение удалено: здесь можно писать не больше {limit} в день. Следующее – после {next_at}."
            },
            'week': {
                'en': "Your message was removed: members post up to {limit} a week here. Next one after {next_at}.",
                'ru': "Сообщение удалено: здесь можно писать не больше {limit} в неделю. "
                      "Следующее – после {next_at}."
            },
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
                    "Ответьте <code>/allow</code> на сообщение участника или отправьте <code>/allow @ник</code>. "
                    "На срок: <code>/allow @ник 7d</code>"
            },
            'deny': {
                'en': "Reply <code>/deny</code> to a member's message, or send <code>/deny @nick</code>",
                'ru': "Ответьте <code>/deny</code> на сообщение участника или отправьте <code>/deny @ник</code>"
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
        'auto_connect_failed': {
            'en': "Could not connect <b>{chat_name}</b>: {reason}",
            'ru': "Не удалось подключить <b>{chat_name}</b>: {reason}"
        },
        'needs_admin': {
            'en':
                "The bot is in <b>{chat_name}</b>, but cannot delete messages yet. Make it an admin with the right "
                "to delete messages (and to restrict members), and it will connect the group by itself.",
            'ru':
                "Бот в группе <b>{chat_name}</b>, но пока не может удалять сообщения. Сделайте его администратором "
                "с правом удалять сообщения (и ограничивать участников), и он сам подключит группу."
        },
    },
    'tariffs': {
        # HTML, under the list of tariffs
        'features': {
            'en':
                "<b>Every tariff</b>: a whitelist, alerts with \"Allow\" in one tap, commands in the group.\n"
                "<b>Paid tariffs</b> add access for 7 or 30 days and posting limits (1 a day, 3 a week…).",
            'ru':
                "<b>На любом тарифе</b>: белый список, оповещения с \"Разрешить\" в одно нажатие, команды в группе.\n"
                "<b>Платные тарифы</b> добавляют доступ на 7 или 30 дней и лимит постов (1 в день, 3 в неделю…)."
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
