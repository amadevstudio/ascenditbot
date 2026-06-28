from project import constants

emoji_codes = {
    'new': '🆕',  # \U0001F195
    'chat': '👥',
    'sos': '🆘',
    'credit_card': '💳',
    'money_with_wings': '💸',
    'down_arrow': '⬇️',
    'heavy_check_mark': '✅',
    'cross_mark': '❌',
    'warning_sign': '⚠️',
    'wastebasket': '🗑️',
    'bar_chart': '📊',
    'gold_medal': '🥇',
    'silver_medal': '🥈',
    'bronze_medal': '🥉',
    'crown': '👑',
    'gear': '⚙️',
    'email': '📧',
    'CL': '🆑',
    'magic_wand': '🪄',
    'hourglass': '⌛️'
}

local_lang_based_links = {
    'add_chat': {
        'anon_admin_example': {
            'template': "./public/anonim_admin_example_{language_code}.jpg",
            'default': "./public/anonim_admin_example_ru.jpg"
        }
    },
}
links = {
    'instructions': {
        'add_chat': {
            'en': "https://light-balloon-833.notion.site/Instruction-06077358bb4a40ba95903b6b317c11a4",
            'ru': "https://light-balloon-833.notion.site/3c8c1d5c03644a14975c4aaa26d06a1b"
        }
    }
}

routed_messages = {
    'buttons': {
        'back': {
            'en': "Back",
            'ru': "Назад"
        },
        'cancel': {
            'en': "Cancel",
            'ru': "Отмена"
        },
        'go_to_settings': {
            'en': "Go to settings",
            'ru': "Перейти к настройкам"
        },
        'menu': {
            'en': "Menu",
            'ru': "Меню",
        },
        'my_chats': {
            'en': f"{emoji_codes.get('chat', '')} My chats",
            'ru': f"{emoji_codes.get('chat', '')} Мои группы"
        },
        'add_chat': {
            'en': f"{emoji_codes.get('new', '')} Add chat",
            'ru': f"{emoji_codes.get('new', '')} Добавить группу"
        },
        'help': {
            'en': f"{emoji_codes.get('sos', '')} Help",
            'ru': f"{emoji_codes.get('sos', '')} Помощь"
        },
        'subscription': {
            'en': f"{emoji_codes.get('credit_card', '')} Subscription",
            'ru': f"{emoji_codes.get('credit_card', '')} Подписка"
        },
        'settings': {
            'en': f"{emoji_codes.get('gear', '')} Settings",
            'ru': f"{emoji_codes.get('gear', '')} Настройки"
        },
        'clear_search': {
            'en': f"{emoji_codes.get('CL', '')} Clear search",
            'ru': f"{emoji_codes.get('CL', '')} Очистить поиск"
        }
    },
    'errors': {
        'state_data_none': {
            'en': "Your state has been reset, please start over with /menu",
            'ru': "Ваше состояние сброшено, пожалуйста, начните сначала с помощью команды /menu"
        },
        'unexpected': {
            'en':
                "Unhandled error, please contact the bot administration and tell us about the error "
                "and the time it occurred.",
            'ru':
                "Необрабатываемая ошибка, пожалуйста, свяжитесь с администрацией бота и расскажите об ошибке "
                "и времени, когда она возникла."
        },
        'user_none': {
            'en':
                "There is no entry about you in the database.\nIf you are using the bot in a chat, "
                "then go to a private dialogue with the bot: the chat cannot be an administrator, "
                "management functionality from chats is under development.\nIf you are already in a private dialogue, "
                "enter the command /start and try again!",
            'ru':
                "Запись о вас отсутствует в базе данных.\nЕсли вы используете бота в чате или группе, "
                "то перейдите в личный диалог с ботом: группа не может быть администратором, функционал управления "
                "из групп в разработке.\nЕсли вы уже в личном диалоге, введите команду /start и попробуйте ещё раз!"
        },
    },
    'user': {
        'errors': {
            'email_is_none': {
                'en': "To replenish the balance, you must enter an email! Enter it on the /settings page",
                'ru': "Для пополнения баланса необходимо ввести электронную почту! Заполните её на странице /settings"
            }
        }
    },

    'welcome': {
        'introduction': {
            'en':
                "Welcome! This bot allows you to create whitelists for chats, and will learn many more useful things "
                "in the future.\n\n"
                "Save time with @{bot_name}!"
                .format(bot_name=constants.bot_nickname),
            'ru':
                "Добро пожаловать! Этот бот позволяет создавать белые списки для групп, а в будущем научится ещё "
                "множеству полезных вещей.\n\n"
                "Экономьте время с помощью @{bot_name}!"
                .format(bot_name=constants.bot_nickname)
        },
        'lets_begin': {
            'en': "Let's start!",
            'ru': "Начнём!"
        }
    },
    'menu': {
        'text': {
            'en': "<b>Main menu</b>, navigate to the desired section using the buttons below "
                  "or type / to preview commands",
            'ru': "<b>Главное меню</b>, перейдите в нужный раздел с помощью кнопок ниже "
                  "или введите / для предпросмотра команд"
        }
    },
    'help': {
        'text': {
            'en':
                f"@{constants.bot_nickname}\n\n"
                "This bot allows you to create whitelists for chats,"
                " and will learn many more useful things in the future\n\n"
                "In order to start, you must be the owner of the chat."
                "To add her, open /add_chat and follow the instructions."
                " Added chats are available in /my_chats where you can manage it and users\n\n"
                "In order to use all the features, you must have a subscription."
                " All subscription information is on /subscription",
            'ru':
                f"@{constants.bot_nickname}\n\n"
                "Этот бот позволяет создавать белые списки для групп,"
                " а в будущем научится ещё множеству полезных вещей\n\n"
                "Для того, чтобы начать, вы должны быть владельцем группы."
                " Чтобы добавить её, откройте /add_chat и следуйте инструкциям."
                " Добавленные группы доступны в /my_chats, где вы можете управлять ей и пользователями\n\n"
                "Для того, чтобы использовать все возможности, у вас должна быть подписка."
                " Вся информация по подписке находится на /subscription"
        },
        'privacy': {
            "ru": "Мы храним некоторые ваши данные для предоставления сервиса: telegram id, ваше имя, никнейм, "
                  "язык, а также все указанные в боте данные, например, список ваших чатов и белый список, "
                  "идентификаторы чатов и так далее.\n\n"
                  "Мы ни с кем не делимся этими данными кроме случаев, когда это используется в интерфейсе бота.",
            "en": "We store some of your data to provide the service: telegram id, your name, nickname, language, "
                  "as well as all the data specified in the bot, for example, a list of your chats, "
                  "chats identifiers, and so on.\n\n"
                  "We do not share this data with anyone except when it is used in the bot interface."
        }
    },

    'access': {
        'chat': {
            'errors': {
                'unknown': {
                    'en': "An unknown error occurred while checking access, contact the bot administration!",
                    'ru': "Возникла неизвестная ошибка при проверке доступа, свяжитесь с администрацией бота!"
                },
                'not_member': {
                    'en':
                        "The bot is not a member of the chat. "
                        "Add him as an administrator with the ability to delete messages and try again!",
                    'ru':
                        "Бот не является членом группы. "
                        "Добавьте его в качестве администратора с возможностью удаления сообщений и попробуйте ещё раз!"
                },
                'not_found': {
                    'en':
                        "The chat not found."
                        "Add the bot as an administrator to it and check if the id is correct.",
                    'ru':
                        "Группа не найдена. "
                        "Добавьте в неё бота в качестве администратора и проверьте правильность идентификатора."
                },
                'not_admin': {
                    'en':
                        "Bot is not a chat admin."
                        "Make him an administrator with the ability to delete messages and try again!",
                    'ru':
                        "Бот не является администратором группы. "
                        "Сделайте его администратором с возможностью удаления сообщений и попробуйте ещё раз!"
                },
                'cant_edit_messages': {
                    'en':
                        "Bot is admin, but can't delete posts. "
                        "Give him the ability to delete messages and try again!",
                    'ru':
                        "Бот администратор, но не может удалять сообщения. "
                        "Добавьте ему возможность удаления сообщений и попробуйте ещё раз!"
                },
                'user_not_admin': {
                    'en':
                        "We can't find you on the admin list. Please make sure you forward the message from the chat, "
                        "where you are an administrator with permission to delete messages.",
                    'ru':
                        "Мы не можем найти вас в списке администраторов. Убедитесь, что пересылаете сообщение из чата, "
                        "в котором вы администратор с правами удаления сообщений."
                },
                'user_cant_edit_messages': {
                    'en':
                        "You don't have permission to delete messages. Make sure you're forwarding a message from a"
                        " chat, in which you have such rights.",
                    'ru':
                        "У вас нет прав на удаление сообщений. Убедитесь, что пересылаете сообщение из чата, "
                        "в котором у вас есть такие права."
                },
                'creator_must_add': {
                    'en': "In order to administer a chat, the owner must first add it to the bot",
                    'ru': "Чтобы администрировать группу, сначала владелец должен добавить её в бот"
                },
                'owner_must_delete': {
                    'en': "Only the chat owner can delete it from the bot",
                    'ru': "Удалить группу из бота может только владелец группы"
                },
                'creator_dont_subscribed': {
                    'en':
                        "In order for other admins to manage the chat, the owner must have a subscription to the bot"
                        "and have a sufficient subscription level",
                    'ru':
                        "Чтобы другие администраторы могли управлять группой, владелец должен иметь подписку на бота"
                        " и иметь достаточный уровень подписки"
                },
                'subscription_limit_violation': {
                    'en':
                        "Sorry, your subscription level is not sufficient for this chat to work."
                        " More details on the page Subscription /subscription",
                    'ru':
                        "К сожалению, ваш уровень подписки недостаточен, чтобы это группа работала."
                        " Подробнее на странице Подписка /subscription"
                }
            }
        }
    },
    'add_chat': {
        'instruction': {
            'en':
                "To add a chat to a bot, follow these simple steps:\n\n"
                "1. Make the bot an administrator of your chat"
                "with the ability to edit messages and view other administrators\n\n"
                "2. While this message is active (the last one in the chat),"
                " click on the button below and select a chat.\n"
                "Another way: send the chat ID or just send a message to the bot from it,"
                f" written on behalf of the chat (anonymous administrator)\n\n"
                f"<a href=\"{links['instructions']['add_chat']['en']}\">Open detailed instructions</a>",
            'ru':
                "Чтобы добавить группу в бота, следуйте простым шагам:\n\n"
                "1. Сделайте бота администратором вашей группы"
                " с возможностью редактирования сообщений и просмотром других администраторов\n\n"
                "2. Пока это сообщение активно (последнее в чате) нажмите на кнопку снизу и выберите группу.\n"
                "Другой способ: пришлите идентификатор группы или просто перешлите боту сообщение из неё,"
                f" написанное от лица группы (анонимный администратор)\n\n"
                f"<a href=\"{links['instructions']['add_chat']['ru']}\">Открыть подробную инструкцию</a>"
        },
        'add_chat_reply_button_text': {
            'en': emoji_codes.get('down_arrow', '') * 3 + " Or click on the button below:",
            'ru': emoji_codes.get('down_arrow', '') * 3 + " Или нажмите на кнопку ниже:"
        },
        'add_chat_reply_button': {
            'en': f"{emoji_codes.get('heavy_check_mark', '')} Select chat {emoji_codes.get('magic_wand', '')}",
            'ru': f"{emoji_codes.get('heavy_check_mark', '')} Выбрать группу {emoji_codes.get('magic_wand', '')}"
        },
        'success': {
            'en': "Chat {chat_name} has been added successfully!\n\nPlease add another one or go to settings.",
            'ru': "Группа {chat_name} была успешно добавлена!\n\nДобавьте ещё одну или перейдите к настройкам."
        },
        'subscription_limit_violation': {
            'en': "Your subscription level does not allow you to add more chats, read more /subscription",
            'ru': "Ваш уровень подписки не позволяет добавить больше чатов, подробнее /subscription"
        },
        'errors': {
            'connection_exists': {
                'en': "chat already added. Add another one or go to settings.",
                'ru': "Группа уже добавлена. Добавьте другую или перейдите к настройкам."
            },
        }
    },
    'my_chats': {
        'list': {
            'main': {
                'en': f"{emoji_codes.get('chat', '')} My chats",
                'ru': f"{emoji_codes.get('chat', '')} Мои группы"
            },
            'chat_button': {
                'active': {
                    'en': emoji_codes.get('heavy_check_mark', '') + " {chat_name}",
                    'ru': emoji_codes.get('heavy_check_mark', '') + " {chat_name}"
                },
                'inactive': {
                    'en': "{chat_name}",
                    'ru': "{chat_name}"
                },
                'disabled': {
                    'en': emoji_codes.get('warning_sign', '') + " {chat_name}",
                    'ru': emoji_codes.get('warning_sign', '') + " {chat_name}"
                },
                'not_found_tg': {
                    'en': emoji_codes.get('sos', '') + emoji_codes.get('warning_sign', '') + " Not found!",
                    'ru': emoji_codes.get('sos', '') + emoji_codes.get('warning_sign', '') + " Не найдена!"
                }
            }
        },
        'errors': {
            'empty': {
                'en': "You don't have any chats, add the first one using the menu item 'Add chat'",
                'ru': "У вас нет групп, добавьте первую с помощью пункта меню 'Добавить группу'"
            },
            'empty_search': {
                'en': "Chats not found, narrow your search",
                'ru': "Групп не найдено, сузьте поиск"
            }
        }
    },
    'chat': {
        'show': {
            'text': {
                'en': emoji_codes.get('chat', '') + " {chat_name}",
                'ru': emoji_codes.get('chat', '') + " {chat_name}"
            },
            'disabled': {
                'en':
                    emoji_codes.get('warning_sign', '')
                    + "chat disabled, please improve your conditions. More details on the page /subscription",
                'ru':
                    emoji_codes.get('warning_sign', '')
                    + " Группа отключена, улучшите ваши условия. Подробнее на странице /subscription"
            },
            'whitelist_button': {
                'en': "List of allowed users",
                'ru': "Белый список пользователей"
            },
            'add_to_whitelist_button': {
                'en': "Add to allowed users",
                'ru': "Добавить в белый список"
            },
            'restriction_duration_button': {
                'en': "Restriction: {duration} min",
                'ru': "Ограничение: {duration} мин"
            },
            'active_button': {
                'active': {
                    'en': emoji_codes.get('heavy_check_mark', '') + " Chat is connected",
                    'ru': emoji_codes.get('heavy_check_mark', '') + " Чат подключён"
                },
                'inactive': {
                    'en': emoji_codes.get('cross_mark', '') + " Chat disabled",
                    'ru': emoji_codes.get('cross_mark', '') + " Чат отключён"
                }
            },
            'delete_button': {
                'initial': {
                    'en': emoji_codes.get('wastebasket', '') + " Delete chat",
                    'ru': emoji_codes.get('wastebasket', '') + " Удалить группу"
                },
                'deleting': {
                    'en': emoji_codes.get('warning_sign', '') + " Confirm deletion?",
                    'ru': emoji_codes.get('warning_sign', '') + " Подтвердить удаление?"
                }
            }
        },
        'delete': {
            'confirm': {
                'en': "Click the button again to delete",
                'ru': "Для удаления нажмите на кнопку ещё раз"
            }
        },
        'restriction_duration': {
            'text': {
                'en':
                    "Current restriction time: <b>{duration} min</b>\n\n"
                    "Send a number from {min_duration} to {max_duration}. "
                    "Users outside the allowed list will be restricted for this time after their message is deleted.",
                'ru':
                    "Текущее время ограничения: <b>{duration} мин</b>\n\n"
                    "Пришлите число от {min_duration} до {max_duration}. "
                    "Пользователи вне белого списка будут ограничены на это время после удаления сообщения."
            },
            'success': {
                'en': "Restriction time saved: {duration} min",
                'ru': "Время ограничения сохранено: {duration} мин"
            },
            'success_with_warning': {
                'en': "Restriction time saved: {duration} min, but temporary restriction needs attention.",
                'ru': "Время ограничения сохранено: {duration} мин, но временное ограничение требует внимания."
            },
            'errors': {
                'invalid': {
                    'en': "Send a whole number from {min_duration} to {max_duration}",
                    'ru': "Пришлите целое число от {min_duration} до {max_duration}"
                }
            },
            'warnings': {
                'restriction_supergroup_required': {
                    'en':
                        "Temporary restriction works only in supergroups. "
                        "Messages outside the allowed list will still be deleted.",
                    'ru':
                        "Временное ограничение работает только в супергруппах. "
                        "Сообщения вне белого списка всё равно будут удаляться."
                },
                'cant_restrict_members': {
                    'en':
                        "The bot needs administrator permission to restrict members. "
                        "Messages outside the allowed list will still be deleted.",
                    'ru':
                        "Боту нужны права администратора на ограничение участников. "
                        "Сообщения вне белого списка всё равно будут удаляться."
                },
                'not_member': {
                    'en':
                        "The bot is not a chat member. "
                        "Messages can be moderated again after the bot is added as an administrator.",
                    'ru':
                        "Бота нет в группе. "
                        "Модерация продолжит работать после добавления бота администратором."
                },
                'not_found': {
                    'en':
                        "The chat was not found. "
                        "Check that the bot is still in the chat and has administrator permissions.",
                    'ru':
                        "Группа не найдена. "
                        "Проверьте, что бот всё ещё в группе и имеет права администратора."
                },
                'not_admin': {
                    'en':
                        "The bot must be a chat administrator. "
                        "Messages outside the allowed list will be deleted only when delete permission is available.",
                    'ru':
                        "Бот должен быть администратором группы. "
                        "Сообщения вне белого списка будут удаляться только при наличии права удаления."
                },
                'cant_edit_messages': {
                    'en':
                        "The bot needs permission to delete messages. "
                        "Temporary restriction is an addition to deletion, not a replacement.",
                    'ru':
                        "Боту нужны права на удаление сообщений. "
                        "Временное ограничение дополняет удаление, а не заменяет его."
                },
                'unknown': {
                    'en':
                        "Restriction permissions could not be checked. "
                        "Messages outside the allowed list will still be deleted when possible.",
                    'ru':
                        "Не удалось проверить права на ограничение. "
                        "Сообщения вне белого списка всё равно будут удаляться, если это возможно."
                }
            }
        },
        'add_to_whitelist': {
            'text': {
                'en':
                    emoji_codes.get('chat', '') +
                    " To add users, send their nicknames separated by a space, for example\n"
                    "<code>mike christie</code>",
                'ru':
                    emoji_codes.get('chat', '') +
                    " Чтобы добавить пользователей, пришлите их никнеймы через пробел, например\n"
                    "<code>mike christie</code>"
            },
            'success': {
                'en': "Nickname {nickname} saved! Add another one or go back",
                'ru': "Никнейм {nickname} сохранён! Добавьте ещё или вернитесь назад"
            },
            'success_plural': {
                'en': "Nicknames are saved! Add another one or go back",
                'ru': "Никнеймы сохранены! Добавьте ещё или вернитесь назад"
            }
        },
        'errors': {
            'not_found': {
                'en': "Chat not found, try adding it to the bot again!",
                'ru': "Чат не найден, попробуйте добавить его в бота ещё раз!"
            },
            'not_found_tg': {
                'en':
                    "Looks like the chat has been deleted or the bot isn't in it."
                    "Check if the bot is a chat admin with the ability to delete messages",
                'ru':
                    "Похоже, чат удалён или бота в нём нет."
                    " Проверьте, является ли бот администратором чата с возможностью удаления сообщений"
            }
        }
    },
    'whitelist': {
        'list': {
            'text': {
                'en': "chat allowed List",
                'ru': "Белый список группы"
            },
            'button': {
                'active': {
                    'en': emoji_codes.get('heavy_check_mark', '') + " {nickname}",
                    'ru': emoji_codes.get('heavy_check_mark', '') + " {nickname}"
                },
                'inactive': {
                    'en': "{nickname}",
                    'ru': "{nickname}"
                }
            }
        },
        'errors': {
            'empty': {
                'en': "Now the list is empty. Please add a user first",
                'ru': "Сейчас список пуст. Сначала добавьте пользователя"
            },
            'empty_search': {
                'en': "No users found, narrow your search",
                'ru': "Пользователей не найдено, сузьте поиск"
            }
        }
    },
    'allowed_user': {
        'show': {
            'text': {
                'en': emoji_codes.get('chat', '') + " {chat_name}\nUser: t.me/{nickname}",
                'ru': emoji_codes.get('chat', '') + " {chat_name}\nПользователь: t.me/{nickname}"
            },
            'active_button': {
                'active': {
                    'en': emoji_codes.get('heavy_check_mark', '') + " Can write",
                    'ru': emoji_codes.get('heavy_check_mark', '') + " Может писать"
                },
                'inactive': {
                    'en': emoji_codes.get('cross_mark', '') + " Messages are deleted",
                    'ru': emoji_codes.get('cross_mark', '') + " Сообщения удаляются"
                }
            },
            'delete_button': {
                'initial': {
                    'en': emoji_codes.get('wastebasket') + " Remove from allowed",
                    'ru': emoji_codes.get('wastebasket') + " Удалить из белого списка"
                },
                'deleting': {
                    'en': emoji_codes.get('warning sign', '') + " Confirm deletion?",
                    'ru': emoji_codes.get('warning_sign', '') + " Подтвердить удаление?"
                }
            }
        },
        'delete': {
            'confirm': {
                'en': "Click the button again to delete",
                'ru': "Для удаления нажмите на кнопку ещё раз"
            }
        }
    },
    'subscription': {
        'info_block': {
            'text': {
                'en': "{tariff_name}\n{balance} {currency_code}\n{max_channels}",
                'ru': "{tariff_name}\n{balance} {currency_code}\n{max_channels}"
            },
            'of_channels': {
                'en': {
                    1: 'chat',
                    2: 'chats',
                    5: 'chats'
                },
                'ru': {
                    1: 'чат',
                    2: 'чата',
                    5: 'чатов'
                }
            },
            'days_countable': {
                'en': {
                    1: 'day',
                    2: 'days',
                    5: 'days'
                },
                'ru': {
                    1: 'день',
                    2: 'дня',
                    5: 'дней'
                }
            },
            'days_left': {
                'en': {
                    1: '{days_left} day left',
                    2: '{days_left} days left',
                    5: '{days_left} days left'
                },
                'ru': {
                    1: 'Остался {days_left} день',
                    2: 'Осталось {days_left} дня',
                    5: 'Осталось {days_left} дней'
                }
            },
            'less_than_one_day': {
                'en': "Less than 1 day left",
                'ru': "Осталось менее 1 дня"
            },
            'balance': {
                'en': 'Balance',
                'ru': 'Баланс'
            },
            'payment_currency': {
                'en': 'Tariff payment currency',
                'ru': 'Валюта оплаты тарифа'
            },
            'not_enough_for_renewal': {
                'en': "Insufficient Funds to Renew",
                'ru': "Недостаточно средств для продления"
            },
            'unlimited': {
                'en': "Not limited",
                'ru': "Не ограничено"
            },
        },
        'show': {
            'text': {
                'en':
                    f"{emoji_codes.get('credit_card', '')} Subscription\n\n"
                    "A subscription allows you to moderate more chats and access new bot features."
                    " Familiarize yourself with the tariffs by the button \"Select tariff\","
                    " and then replenish the balance for the required amount using the button \"Top up\"",
                'ru':
                    f"{emoji_codes.get('credit_card', '')} Подписка\n\n"
                    "Подписка позволяет модерировать больше чатов и получить доступ к новым функциям бота."
                    " Ознакомьтесь с тарифами по кнопке \"Выбрать тариф\","
                    " а затем пополните баланс на нужную сумму с помощью кнопки \"Пополнить\""
            },
            'balance_warning': {
                'en':
                    emoji_codes.get('warning_sign', '') + "Warning!"
                                                          " Any currency on the balance in the bot system is virtual points,"
                                                          " which are not considered real currency and belong to the owner of the bot",
                'ru':
                    emoji_codes.get('warning_sign', '') + " Внимание!"
                                                          " Любая валюта на балансе в системе бота – это виртуальные очки, "
                                                          "которые не считаются настоящей валютой и принадлежат владельцу бота"
            }
        },
        'referral': {
            'en':
                "Invite friends and get bonuses! If your referral replenishes the balance, then the duration of your"
                f" tariff will be incremented by {int(constants.referred_days_part * 100)}% of the number of days"
                " for which the amount of replenishment would be enough, but no more than"
                f" {int(constants.tariff_duration_days * constants.referred_days_part)}."
                "\nSend them this link:\n{referral_link}",
            'ru':
                "Приглашайте друзей и получайте бонусы! Если ваш реферал пополнит баланс, то длительность вашего тарифа"
                f" будет увеличена на {int(constants.referred_days_part * 100)}% того количества дней,"
                " на которое бы хватило суммы пополнения, но не больше"
                f" {int(constants.tariff_duration_days * constants.referred_days_part)}."
                "\nОтправьте им эту ссылку:\n{referral_link}"
        },
        'buttons': {
            'choose_tariff': {
                'en': f"{emoji_codes.get('bar_chart', '')} Select tariff",
                'ru': f"{emoji_codes.get('bar_chart', '')} Выбрать тариф"
            },
            'fund': {
                'en': f"{emoji_codes.get('money_with_wings', '')} Top up",
                'ru': f"{emoji_codes.get('money_with_wings', '')} Пополнить"
            }
        },
        'free_trial': {
            'en': "<b>Try the bot for free!</b> You have a trial period included, more details: /subscription",
            'ru': "<b>Попробуйте бота бесплатно!</b> Вам включён пробный период, подробнее: /subscription"
        },
        'updated': {
            'en': "Subscription updated!",
            'ru': "Подписка обновлена!"
        },
        'errors': {
            'not_enough_balance': {
                'en': "There are not enough funds on the balance to switch to the best tariff",
                'ru': "Недостаточно средств на балансе для перехода на лучший тариф"
            },
            'already_chosen': {
                'en': "Tariff already selected",
                'ru': "Тариф уже выбран"
            }
        },
        'updates': {
            'prolonged': {
                'en': emoji_codes.get('heavy_check_mark', '') + " Your subscription has been renewed!",
                'ru': emoji_codes.get('heavy_check_mark', '') + " Ваша подписка продлена!"
            },
            'non-prolongable': {
                'en':
                    emoji_codes.get('warning_sign', '') + "Not enough funds for next renewal!"
                                                          " Top up your balance to continue using the bot. More info /subscription",
                'ru':
                    emoji_codes.get('warning_sign', '') + " Недостаточно средств для следующего продления!"
                                                          " Пополните баланс, чтобы продолжать пользоваться ботом. Подробнее /subscription"
            },
            'disabled': {
                'en':
                    emoji_codes.get('warning_sign', '') +
                    " Insufficient funds to renew!\n\n"
                    "Your subscription is disabled. To keep the bot running, top up your account and select a plan",
                'ru':
                    emoji_codes.get('warning_sign', '') +
                    " Недостаточно средств для продления!\n\n"
                    "Ваша подписка отключена. Чтобы бот продолжал работать, пополните счёт и выберите тариф"
            }
        },
        'fund': {
            'page': {
                'en':
                    "Select the balance currency. Then enter the amount or click on one of the buttons with the cost of the"
                    " bot's tariffs. After that, follow the payment instructions."
                    " If everything goes well, the bot will send you a notification\n\n"
                    "The current mail <b>{email}</b> is important, it will receive a payment receipt",
                'ru':
                    "Выберите валюту баланса. Затем введите сумму или нажмите на одну из кнопок со стоимостями тарифов бота."
                    " После этого следуйте инструкциям оплаты."
                    " Если всё пройдёт успешно, бот пришлёт вам уведомление\n\n"
                    "Важа текущая почта <b>{email}</b>, на неё придёт чек об оплате"
            },
            'currency_page': {
                'en': "Top up {currency} balance",
                'ru': "Пополнение баланса {currency}"
            },
            'fund_link_message': {
                'en': "To replenish your account, follow the link\n{link}",
                'ru': "Для пополнения счёта перейдите по ссылке\n{link}"
            },
            'telegram_stars': {
                'invoice_title': {
                    'en': "Telegram Stars balance",
                    'ru': "Баланс Telegram Stars"
                },
                'invoice_description': {
                    'en': "Top up your bot balance with {amount} Telegram Stars",
                    'ru': "Пополнение баланса бота на {amount} Telegram Stars"
                },
                'invoice_sent': {
                    'en': "Telegram Stars invoice sent",
                    'ru': "Счёт Telegram Stars отправлен"
                },
                'checkout_error': {
                    'en': "The payment cannot be processed. Please try again or contact the bot administrator.",
                    'ru': "Платёж не может быть обработан. Попробуйте ещё раз или свяжитесь с администратором бота."
                }
            },
            'success_payment': {
                'en': "Successful payment!",
                'ru': "Успешная оплата!"
            },
            'from_referral': {
                'initialed': {
                    'en': "User just signed up using your referral link!",
                    'ru': "Пользователь только что зарегистрировался по вашей реферальной ссылке!"
                },
                'prolonged': {
                    'en': "Your referral has replenished the balance, as a reward your tariff has been extended!",
                    'ru': "Ваш реферал пополнил баланс, в качестве награды ваш тариф продлен!"
                }
            },
            'errors': {
                'wrong_amount': {
                    'en': "The amount entered is incorrect, please try again",
                    'ru': "Сумма введена неверно, попробуйте ещё раз"
                },
                'wrong_currency': {
                    'en': "Wrong currency is set, please contact the bot administrator",
                    'ru': "Установлена неверная валюта, пожалуйста, свяжитесь с администратором бота"
                },
                'wrong_signature': {
                    'en':
                        "Payment notification received, but the security signature is invalid."
                        " Please contact the bot administrator",
                    'ru':
                        "Получено уведомление об оплате, но подпись безопасности неверная."
                        " Пожалуйста, свяжитесь с администратором бота"
                },
                'wrong_currency_income': {
                    'en':
                        "Payment notification received, but currencies are different."
                        " Please contact the bot administrator",
                    'ru':
                        "Получено уведомление об оплате, но валюты отличаются."
                        " Пожалуйста, свяжитесь с администратором бота"
                }
            }
        }
    },
    'tariffs': {
        'index': {
            'en':
                f"{emoji_codes.get('bar_chart', '')} Tariffs\n\n"
                "Attention! When changing the tariff, the difference for the remaining days is calculated:\n"
                "● with a positive value when choosing a cheaper tariff;\n"
                "● with a negative when choosing a more expensive one.\n\n"
                f"{emoji_codes.get('warning_sign', '')} However, the amount for the current day will be charged again!",
            'ru':
                f"{emoji_codes.get('bar_chart', '')} Тарифы\n\n"
                "Внимание! При смене тарифа начисляется разница за оставшиеся дни:\n"
                "● с положительным значением при выборе более дешёвого тарифа;\n"
                "● с отрицательным при выборе более дорогого.\n\n"
                f"{emoji_codes.get('warning_sign', '')} Однако сумма за текущий день будет списана ещё раз!"
        },
        'current': {
            'en': "<b>Your current conditions</b>",
            'ru': "<b>Ваши текущие условия</b>"
        },
        'list': {
            'wrapper': {
                'en': "{tariff_text} tariff",
                'ru': "{tariff_text} тариф"
            },
            0: {
                'en': "No subscription",
                'ru': "Без подписки"
            },
            1: {
                'en': emoji_codes.get('bronze_medal', '') + " Initial",
                'ru': emoji_codes.get('bronze_medal', '') + " Начальный"
            },
            2: {
                'en': emoji_codes.get('silver_medal', '') + " Advanced",
                'ru': emoji_codes.get('silver_medal', '') + " Продвинутый"
            },
            3: {
                'en': emoji_codes.get('gold_medal', '') + " Professional",
                'ru': emoji_codes.get('gold_medal', '') + " Профессиональный"
            },
            4: {
                'en': emoji_codes.get('crown', '') + " Corporate",
                'ru': emoji_codes.get('crown', '') + " Корпоративный"
            }
        },
        'info': {
            'selected': {
                'en': "(selected)",
                'ru': "(выбран)"
            }
        }
    },
    'settings': {
        'page': {
            'en': f"{emoji_codes.get('gear', '')} Settings",
            'ru': f"{emoji_codes.get('gear', '')} Настройки"
        },
        'buttons': {
            'email': {
                'en': f"{emoji_codes.get('email', '')} E-Mail",
                'ru': f"{emoji_codes.get('email', '')} Почта"
            },
            'currency': {
                'en': f"{emoji_codes.get('credit_card', '')} Tariff payment currency",
                'ru': f"{emoji_codes.get('credit_card', '')} Валюта оплаты тарифа"
            }
        },
        'email': {
            'page': {
                'en':
                    f"{emoji_codes.get('email', '')} Email Setup\n"
                    "Current email: {email}\n\n"
                    "Send mail to update it",
                'ru':
                    f"{emoji_codes.get('email', '')} Настройка почты\n"
                    "Текущая почта: {email}\n\n"
                    "Отправьте почту, чтобы обновить её"
            },
            'empty': {
                'en': "empty",
                'ru': "не установлена"
            }
        },
        'currency': {
            'page': {
                'en':
                    f"{emoji_codes.get('credit_card', '')} Tariff payment currency\n"
                    "Current currency: {currency}\n\n"
                    "This affects tariff changes and future renewals. Existing balances are not converted.",
                'ru':
                    f"{emoji_codes.get('credit_card', '')} Валюта оплаты тарифа\n"
                    "Текущая валюта: {currency}\n\n"
                    "Это влияет на смену тарифа и будущие продления. Существующие балансы не конвертируются."
            }
        }
    },

    'navigation_builder': {
        'actions': {
            'page': {
                'en': "Page",
                'ru':
                    "Страница"
            },
            'of': {
                'en': "of",
                'ru': "из"
            },
            'back': {
                'en': "Go back",
                'ru': "Назад"
            }
        },
        'tips': {
            'tip_send_page_num_to_go': {
                'en': "Tip: send page number to go to it; send text to start searching",
                'ru': "Совет: отправьте номер страницы, чтобы перейти на неё; пришлите текст, чтобы начать поиск"
            }
        },
        'errors': {
            'empty': {
                'en': "No data",
                'ru':
                    "Данных нет"
            },
            'already_on_this_page': {
                'en': "Already on the page",
                'ru': "Эта страница уже открыта"
            },
            'page_does_not_exist': {
                'en': "The page does not exist, try to go to the first",
                'ru': "Страница не существует, попробуйте перейти на первую"
            }
        }
    }
}
