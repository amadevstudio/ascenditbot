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
                "● a message when a stranger writes, with \"Allow\" in one tap\n"
                "● a way in through the bot: newcomers ask or pay you, you confirm in one tap\n\n"
                "One group is free.",
            'ru':
                "Привет! Я слежу за порядком в группе: писать в ней могут только те, кого вы разрешили, "
                "остальные сообщения сразу удаляются.\n\n"
                "Сделан для групп объявлений и рекламы, где право писать чего-то стоит:\n"
                "● белый список по нику, id или пересланному сообщению\n"
                "● доступ на 7 или 30 дней, который сам заканчивается\n"
                "● лимит постов: 1 объявление в день, 3 в неделю и так далее\n"
                "● сообщение, когда пишет посторонний, и \"Разрешить\" в одно нажатие\n"
                "● вход через бота: новые просят доступ или платят вам, вы подтверждаете в одно нажатие\n\n"
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
                "<b>The way in through the bot</b>: on the group's page, \"Way in through the bot\". Whoever is "
                "not on the list gets a link to the group's page in the bot: they ask for access (free) or pick a "
                "term and pay by your link (paid tariffs), and you confirm in one tap.\n\n"
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
                "<b>Вход через бота</b>: на странице группы, \"Вход через бота\". Тем, кто не в списке, бот даёт "
                "ссылку на страницу группы: там просят доступ (бесплатно) или выбирают срок и платят по вашей "
                "ссылке (платные тарифы), а вы подтверждаете в одно нажатие.\n\n"
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
            'access_button': {
                'off': {'en': "🔑 Way in through the bot: off", 'ru': "🔑 Вход через бота: выкл"},
                'request': {'en': "🔑 Way in through the bot: by request", 'ru': "🔑 Вход через бота: по заявке"},
                'paid': {'en': "🔑 Way in through the bot: paid", 'ru': "🔑 Вход через бота: за плату"},
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
    # The way in through the bot (pkg/service/access.py). HTML unless noted
    'access': {
        'term': {
            'one': {'en': "{days} day", 'ru': "{days} день"},
            'few': {'en': "{days} days", 'ru': "{days} дня"},
            'many': {'en': "{days} days", 'ru': "{days} дней"},
            'forever': {'en': "for good", 'ru': "навсегда"},
        },
        # The owner's page of the way in
        'owner': {
            'title': {'en': "🔑 <b>The way in through the bot: {chat_name}</b>",
                      'ru': "🔑 <b>Вход через бота: {chat_name}</b>"},
            'intro_off': {
                'en': "Whoever is not on the whitelist gets a page of the group in the bot, where they can ask for "
                      "access or pay for it. You approve in one tap.\n\nHow do newcomers get in?",
                'ru': "Тем, кто не в белом списке, бот покажет страницу группы: там можно попросить доступ или "
                      "оплатить его. Вы одобряете в одно нажатие.\n\nКак пускать новых?"
            },
            'mode': {
                'request': {'en': "Mode: 📨 by request, free", 'ru': "Режим: 📨 по заявке, бесплатно"},
                'paid': {'en': "Mode: 💳 paid", 'ru': "Режим: 💳 за плату"},
            },
            'prices': {'en': "Prices: {plans}", 'ru': "Цены: {plans}"},
            'prices_none': {'en': "Prices: not set", 'ru': "Цены: не заданы"},
            'payment': {'en': "Payment: {payment}\nYou check the payment and confirm the request.",
                        'ru': "Оплата: {payment}\nВы проверяете оплату и подтверждаете заявку."},
            'payment_none': {'en': "Payment: no way to pay set", 'ru': "Оплата: способ не задан"},
            'payment_provider': {
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
                'ru': "ℹ️ Сейчас в группе пишут все, вход через бота не нужен. Он заработает, когда вы вернёте "
                      "белый список."
            },
            'step': {'en': "<b>Step {step} of 2</b>", 'ru': "<b>Шаг {step} из 2</b>"},
            'buttons': {
                'mode_request': {'en': "📨 By request, free", 'ru': "📨 По заявке, бесплатно"},
                'mode_paid': {'en': "💳 Paid", 'ru': "💳 За плату"},
                'locked': {'en': "🔒 ", 'ru': "🔒 "},
                'prices': {'en': "💰 Prices", 'ru': "💰 Цены"},
                'payment': {'en': "💳 Way to pay", 'ru': "💳 Способ оплаты"},
                'terms': {'en': "✏️ Terms", 'ru': "✏️ Условия"},
                'post': {'en': "📌 Button in the group", 'ru': "📌 Кнопка в группе"},
                'requests': {'en': "📨 Requests ({count})", 'ru': "📨 Заявки ({count})"},
                'to_paid': {'en': "💳 Switch to paid entry", 'ru': "💳 Перейти на платный вход"},
                'to_request': {'en': "📨 Switch to entry by request", 'ru': "📨 Перейти на вход по заявке"},
                'off': {'en': "⏹ Turn the way in off", 'ru': "⏹ Выключить вход"},
                'cancel': {'en': "✖️ Cancel", 'ru': "✖️ Отмена"},
                'use_cryptobot': {'en': "💎 CryptoBot: access opens by itself",
                                  'ru': "💎 CryptoBot: доступ открывается сам"},
                'other_ways': {'en': "⬅️ Other ways", 'ru': "⬅️ Другие способы"},
            },
            'prompt': {
                'prices': {
                    'en': "💰 Send the prices in one message, a line per option: the term and the price.\n\n"
                          "For example:\n<code>7 3\n30 10\nforever 30</code>\n\nThe term can be days, weeks "
                          "or months: <code>month 10$</code>. Currency: ₽, $, €, USDT or TON, {currency} if "
                          "none is named.",
                    'ru': "💰 Пришлите цены одним сообщением, по строке на вариант: срок и цена.\n\nНапример:\n"
                          "<code>7 300\n30 1000\nнавсегда 3000</code>\n\nСрок можно писать днями, неделями, "
                          "месяцами: <code>месяц 1000 ₽</code>. Валюта: ₽, $, €, USDT или TON, без неё – {currency}."
                },
                'payment': {
                    'en': "💳 How do you take payment?\n\n🔗 <b>Your link or details</b>: send them in a message "
                          "(PayPal, Boosty, Tribute, a bank transfer link). A member pays and taps \"I paid\", you "
                          "confirm in one tap.\n\n💎 <b>CryptoBot</b>: payment in crypto; the bot sees it and opens "
                          "access by itself. Tap the button below.",
                    'ru': "💳 Как принимать оплату?\n\n🔗 <b>Своя ссылка или реквизиты</b>: пришлите их сообщением "
                          "(ЮMoney, Boosty, Tribute, ссылка банка на перевод). Участник оплатит и нажмёт \"Я "
                          "оплатил(а)\", а вы подтвердите в одно нажатие.\n\n💎 <b>CryptoBot</b>: оплата "
                          "криптовалютой, бот сам видит оплату и открывает доступ. Нажмите кнопку ниже."
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
                'cryptobot_token': {
                    'en': "❌ CryptoBot did not take the token. Check that you copied all of it and send it again.",
                    'ru': "❌ CryptoBot не принял токен. Проверьте, что скопировали его целиком, и пришлите ещё раз."
                },
            },
            'toasts': {
                'saved': {'en': "Saved", 'ru': "Сохранено"},
                'request_on': {'en': "Entry by request is on", 'ru': "Вход по заявке включён"},
                'paid_on': {'en': "Paid entry is on", 'ru': "Платный вход включён"},
                'off': {'en': "The way in is off", 'ru': "Вход через бота выключен"},
                'posted': {'en': "Posted in the group and pinned", 'ru': "Отправлено в группу и закреплено"},
                'posted_unpinned': {'en': "Posted in the group. Pin it so that everyone sees it.",
                                    'ru': "Отправлено в группу. Закрепите сообщение, чтобы его видели все."},
                'post_failed': {'en': "Could not post in the group: the bot may not send messages there.",
                                'ru': "Не получилось отправить в группу: у бота нет права писать сообщения."},
                'no_requests': {'en': "No requests waiting", 'ru': "Новых заявок нет"},
                'requests_sent': {'en': "The requests are below", 'ru': "Заявки ниже"},
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
        },
        'notice': {
            'en': "Your message is deleted: only members on the list write in this group.\n\nGet access: {link}",
            'ru': "Ваше сообщение удалено: писать в этой группе могут только участники из списка.\n\n"
                  "Получить доступ: {link}"
        },
        # The member's page of the group
        'member': {
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
                'en': "<i>This is @{bot}: it lets into a group only those its owner allows. Your own group: /start</i>",
                'ru': "<i>Это @{bot}: он пускает в группу только тех, кого разрешил владелец. Своя группа: /start</i>"
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
                'en': "💳 <b>{chat_name}</b>: {plan}\n\nPay through @CryptoBot with the button below. Access opens "
                      "by itself, usually within a minute of paying.",
                'ru': "💳 <b>{chat_name}</b>: {plan}\n\nОплатите через @CryptoBot по кнопке ниже. Доступ откроется "
                      "сам, обычно в течение минуты после оплаты."
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
                'request': {'en': "📨 Ask for access", 'ru': "📨 Попросить доступ"},
                'remind': {'en': "🔔 Remind the owner", 'ru': "🔔 Напомнить владельцу"},
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
            'add_chat': {'en': "Connect a group", 'ru': "Подключить группу"},
            'subscription': {'en': "Tariff and payment", 'ru': "Тариф и оплата"},
            'settings': {'en': "Settings", 'ru': "Настройки"},
            'help': {'en': "How it works", 'ru': "Как это работает"},
        },
        'group': {
            'allow': {'en': "Allow a member (in reply or @nick, 7d for a week)",
                      'ru': "Разрешить участнику (ответом или @ник, 7d на неделю)"},
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
                "<b>Paid tariffs</b> add access for 7 or 30 days, posting limits (1 a day, 3 a week…) and paid "
                "entry: newcomers pay you for a term.",
            'ru':
                "<b>На любом тарифе</b>: белый список, оповещения с \"Разрешить\" в одно нажатие, команды в группе, "
                "заявки на доступ через бота.\n"
                "<b>Платные тарифы</b> добавляют доступ на 7 или 30 дней, лимит постов (1 в день, 3 в неделю…) и "
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
