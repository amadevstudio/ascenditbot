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
    'email': '📧'
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
            'en': "",
            'ru': "https://light-balloon-833.notion.site/3c8c1d5c03644a14975c4aaa26d06a1b"
        }
    }
}


routed_messages = {
    'buttons': {
        'back': {
            'en': "",
            'ru': "Назад"
        },
        'cancel': {
            'en': "",
            'ru': "Отмена"
        },
        'go_to_settings': {
            'en': "",
            'ru': "Перейти к настройкам"
        },
        'menu': {
            'en': "",
            'ru': "Меню",
        },
        'my_chats': {
            'en': "",
            'ru': f"{emoji_codes.get('chat', '')} Мои группы"
        },
        'add_chat': {
            'en': "",
            'ru': f"{emoji_codes.get('new', '')} Добавить группу"
        },
        'help': {
            'en': "",
            'ru': f"{emoji_codes.get('sos', '')} Помощь"
        },
        'subscription': {
            'en': "",
            'ru': f"{emoji_codes.get('credit_card', '')} Подписка"
        },
        'settings': {
            'en': "",
            'ru': f"{emoji_codes.get('gear', '')} Настройки"
        }
    },
    'errors': {
        'state_data_none': {
            'en': "",
            'ru':
                "Ваше состояние сброшено, пожалуйста, начните сначала с помощью команды /menu"
        },
        'unexpected': {
            'en': "",
            'ru':
                "Необрабатываемая ошибка, пожалуйста, свяжитесь с администрацией бота и расскажите об ошибке "
                "и времени, когда она возникла."
        },
        'user_none': {
            'en': "",
            'ru':
                "Запись о вас отсутствует в базе данных.\nЕсли вы используете бота в чате или группе, "
                "то перейдите в личный диалог с ботом: группа не может быть администратором, функционал управления "
                "из групп в разработке.\nЕсли вы уже в чате, введите команду /start и попробуйте ещё раз!"
        },
    },
    'user': {
        'errors': {
            'email_is_none': {
                'en': "",
                'ru': "Для пополнения баланса необходимо ввести электронную почту! Заполните её на странице /settings"
            }
        }
    },

    'welcome': {
        'introduction': {
            'en': "",
            'ru':
                "Добро пожаловать! Этот бот позволяет создавать белые списки для групп, а в будущем научится ещё "
                "множеству полезных вещей.\n\n"
                "Экономьте время с помощью @{bot_name}!"
                .format(bot_name=constants.bot_name.lower())
        },
        'lets_begin': {
            'en': "",
            'ru':
                "Начнём!"
        }
    },
    'menu': {
        'text': {
            'en': "",
            'ru': "*Главное меню*, перейдите в нужный раздел с помощью кнопок ниже "
                  "или введите / для предпросмотра команд"
        }
    },
    'help': {
        'text': {
            'en': "",
            'ru':
                f"@{constants.bot_name}\n\n"
                "Этот бот позволяет создавать белые списки для групп,"
                " а в будущем научится ещё множеству полезных вещей\n\n"
                "Для того, чтобы начать, вы должны быть владельцем группы."
                " Чтобы добавить её, откройте /add_chat и следуйте инструкциям."
                " Добавленные группы доступны в /my_chats, где вы можете управлять ей и пользователями\n\n"
                "Для того, чтобы использовать все возможности, у вас должна быть подписка."
                " Вся информация по подписке находится на /subscription"
        }
    },

    'access': {
        'chat': {
            'errors': {
                'unknown': {
                    'en': "",
                    'ru': "Возникла неизвестная ошибка при проверке доступа, свяжитесь с администрацией бота!"
                },
                'not_member': {
                    'en': "",
                    'ru':
                        "Бот не является членом группы. "
                        "Добавьте его в качестве администратора с возможностью удаления сообщений и попробуйте ещё раз!"
                },
                'not_found': {
                    'en': "",
                    'ru':
                        "Группа не найдена. "
                        "Добавьте в неё бота в качестве администратора и проверьте правильность идентификатора."
                },
                'not_admin': {
                    'en': "",
                    'ru':
                        "Бот не является администратором группы. "
                        "Сделайте его администратором с возможностью удаления сообщений и попробуйте ещё раз!"
                },
                'cant_edit_messages': {
                    'en': "",
                    'ru':
                        "Бот администратор, но не может удалять сообщения. "
                        "Добавьте ему возможность удаления сообщений и попробуйте ещё раз!"
                },
                'user_not_admin': {
                    'en': "",
                    'ru':
                        "Мы не можем найти вас в списке администраторов. Убедитесь, что пересылаете сообщение из чата, "
                        "в котором вы администратор с правами удаления сообщений."
                },
                'user_cant_edit_messages': {
                    'en': "",
                    'ru':
                        "У вас нет прав на удаление сообщений. Убедитесь, что пересылаете сообщение из чата, "
                        "в котором у вас есть такие права."
                },
                'creator_must_add': {
                    'en': "",
                    'ru': "Чтобы администрировать группу, сначала владелец должен добавить её в бот"
                },
                'creator_dont_subscribed': {
                    'en': "",
                    'ru':
                        "Чтобы другие администраторы могли управлять группой, владелец должен иметь подписку на бота"
                        " и иметь достаточный уровень подписки"
                },
                'subscription_limit_violation': {
                    'en': "",
                    'ru':
                        "К сожалению, ваш уровень подписки недостаточен, чтобы это группа работала."
                        " Подробнее на странице Подписка /subscription"
                }
            }
        }
    },
    'add_chat': {
        'instruction': {
            'en': "",
            'ru':
                "Чтобы добавить группу в бота, следуйте простым шагам:\n\n"
                "1. Сделайте бота администратором вашей группы"
                " с возможностью редактирования сообщений и просмотром других администраторов\n\n"
                "2. Пока это сообщение активно (последнее в чате), пришлите идентификатор группы"
                " или просто перешлите боту сообщение из неё, написанное от лица группы (анонимный администратор)"
                f" {emoji_codes.get('down_arrow', '') * 3}\n\n"
                f"<a href=\"{links['instructions']['add_chat']['ru']}\">Открыть подробную инструкцию</a>"
        },
        'success': {
            'en': "",
            'ru':
                "Группа {chat_name} была успешно добавлена!\n\nДобавьте ещё одну или перейдите к настройкам."
        },
        'subscription_limit_violation': {
            'en': "",
            'ru': "Ваш уровень подписки не позволяет добавить больше чатов, подробнее /subscription"
        },
        'errors': {
            'connection_exists': {
                'en': "",
                'ru':
                    "Группа уже добавлена. Добавьте другую или перейдите к настройкам."
            },
        }
    },
    'my_chats': {
        'list': {
            'main': {
                'en': "",
                'ru':
                    f"{emoji_codes.get('chat', '')} Мои группы"
            },
            'chat_button': {
                'active': {
                    'en': "",
                    'ru': emoji_codes.get('heavy_check_mark', '') + " {chat_name}"
                },
                'inactive': {
                    'en': "",
                    'ru': "{chat_name}"
                },
                'disabled': {
                    'en': "",
                    'ru': emoji_codes.get('warning_sign', '') + " {chat_name}"
                },
                'not_found_tg': {
                    'en': "",
                    'ru': emoji_codes.get('sos', '') + emoji_codes.get('warning_sign', '') + " Не найдена!"
                }
            }
        },
        'errors': {
            'empty': {
                'en': "",
                'ru':
                    "У вас нет групп, добавьте первую с помощью пункта меню 'Добавить группу'"
            }
        }
    },
    'chat': {
        'show': {
            'text': {
                'en': "",
                'ru': emoji_codes.get('chat', '') + " {chat_name}"
            },
            'disabled': {
                'en': "",
                'ru':
                    emoji_codes.get('warning_sign', '')
                    + " Группа отключена, улучшите ваши условия. Подробнее на странице /subscription"
            },
            'whitelist_button': {
                'en': "",
                'ru':
                    'Белый список пользователей'
            },
            'add_to_whitelist_button': {
                'en': "",
                'ru': 'Добавить в белый список'
            },
            'active_button': {
                'active': {
                    'en': "",
                    'ru': emoji_codes.get('heavy_check_mark', '') + " Чат подключён"
                },
                'inactive': {
                    'en': "",
                    'ru': emoji_codes.get('cross_mark', '') + " Чат отключён"
                }
            }
        },
        'add_to_whitelist': {
            'text': {
                'en': "",
                'ru':
                    emoji_codes.get('chat', '') +
                    " Чтобы добавить пользователя, пришлите его никнейм, например `mike`"
            },
            'success': {
                'en': "",
                'ru': "Никнейм {nickname} сохранён! Добавьте ещё один или вернитесь назад"
            },
            'errors': {
                ''
            }
        },
        'errors': {
            'not_found': {
                'en': "",
                'ru':
                    "Чат не найден, попробуйте добавить его в бота ещё раз!"
            },
            'not_found_tg': {
                'en': "",
                'ru':
                    "Похоже, чат удалён или бота в нём нет."
                    " Проверьте, является ли бот администратором чата с возможностью удаления сообщений"
            }
        }
    },
    'whitelist': {
        'list': {
            'text': {
                'en': "",
                'ru': "Белый список группы"
            },
            'button': {
                'active': {
                    'en': "",
                    'ru': emoji_codes.get('heavy_check_mark', '') + " {nickname}"
                },
                'inactive': {
                    'en': "",
                    'ru': "{nickname}"
                }
            }
        },
        'errors': {
            'empty': {
                'en': "",
                'ru': "Сейчас список пуст. Сначала добавьте пользователя"
            }
        }
    },
    'allowed_user': {
        'show': {
            'text': {
                'en': "",
                'ru': emoji_codes.get('chat', '') + " {chat_name}\nПользователь: @{nickname}"
            },
            'active_button': {
                'active': {
                    'en': "",
                    'ru': emoji_codes.get('heavy_check_mark', '') + " Может писать"
                },
                'inactive': {
                    'en': "",
                    'ru': emoji_codes.get('cross_mark', '') + " Сообщения удаляются"
                }
            },
            'delete_button': {
                'initial': {
                    'en': "",
                    'ru': emoji_codes.get('wastebasket') + " Удалить из белого списка"
                },
                'deleting': {
                    'en': "",
                    'ru': emoji_codes.get('warning_sign', '') + " Подтвердить удаление?"
                }
            }
        },
        'delete': {
            'confirm': {
                'en': "",
                'ru': "Для удаления нажмите на кнопку ещё раз"
            }
        }
    },
    'subscription': {
        'info_block': {
            'text': {
                'en': "",
                'ru':
                    "{tariff_name}\n{balance} {currency_code}\n{max_channels}"
            },
            'of_channels': {
                'en': {},
                'ru': {
                    1: 'чат',
                    2: 'чата',
                    5: 'чатов'
                }
            },
            'days_countable': {
                'en': {},
                'ru': {
                    1: 'день',
                    2: 'дня',
                    5: 'дней'
                }
            },
            'days_left': {
                'en': {},
                'ru': {
                    1: 'Остался {days_left} день',
                    2: 'Осталось {days_left} дня',
                    5: 'Осталось {days_left} дней'
                }
            },
            'balance': {
                'en': {},
                'ru': 'Баланс'
            },
            'not_enough_for_renewal': {
                'en': "",
                'ru': "Недостаточно средств для продления"
            },
            'unlimited': {
                'en': "",
                'ru': "Не ограничено"
            },
        },
        'show': {
            'text': {
                'en': "",
                'ru':
                    f"{emoji_codes.get('credit_card', '')} Подписка\n\n"
                    "Подписка позволяет модерировать больше чатов и получить доступ к новым функциям бота."
                    " Ознакомьтесь с тарифами по кнопке \"Выбрать тариф\","
                    " а затем пополните баланс на нужную сумму с помощью кнопки \"Пополнить\""
            },
            'balance_warning': {
                'en': "",
                'ru':
                    emoji_codes.get('warning_sign', '') + " Внимание!"
                    " Любая валюта на балансе в системе бота – это виртуальные очки, "
                    "которые не считаются настоящей валютой и принадлежат владельцу бота"
            }
        },
        'buttons': {
            'choose_tariff': {
                'en': "",
                'ru': f"{emoji_codes.get('bar_chart', '')} Выбрать тариф"
            },
            'fund': {
                'en': "",
                'ru': f"{emoji_codes.get('money_with_wings', '')} Пополнить"
            }
        },
        'free_trial': {
            'en': "",
            'ru': "*Попробуйте бота бесплатно!* Вам включён пробный период, подробнее: /subscription"
        },
        'updated': {
            'en': "",
            'ru': "Подписка обновлена!"
        },
        'errors': {
            'not_enough_balance': {
                'en': "",
                'ru': "Недостаточно средств на балансе для перехода на лучший тариф"
            },
            'already_chosen': {
                'en': "",
                'ru': "Тариф уже выбран"
            }
        },
        'updates': {
            'prolonged': {
                'en': "",
                'ru': emoji_codes.get('heavy_check_mark', '') + " Ваша подписка продлена!"
            },
            'non-prolongable': {
                'en': "",
                'ru':
                    emoji_codes.get('warning_sign', '') + " Недостаточно средств для следующего продления!"
                    " Пополните баланс, чтобы продолжать пользоваться ботом. Подробнее /subscription"
            },
            'disabled': {
                'en': "",
                'ru':
                    emoji_codes.get('warning_sign', '') +
                    " Недостаточно средств для продления!\n\n"
                    "Ваша подписка отключена. Чтобы бот продолжал работать, пополните счёт и выберите тариф"
            }
        },
        'fund': {
            'page': {
                'en': "",
                'ru':
                    "Для пополнения баланса введите сумму или нажмите на одну из кнопок со стоимостями тарифов бота."
                    " После этого перейдите по ссылке и пополните баланс."
                    " Если всё пройдёт успешно, бот пришлёт вам уведомление\n\n"
                    "Важа текущая почта *{email}*, на неё придёт чек об оплате"
            },
            'fund_link_message': {
                'en': "",
                'ru': "Для пополнения счёта перейдите по ссылке\n{link}"
            },
            'success_payment': {
                'en': "",
                'ru': "Успешная оплата!"
            },
            'errors': {
                'wrong_amount': {
                    'en': "",
                    'ru': "Сумма введена неверно, попробуйте ещё раз"
                },
                'wrong_currency': {
                    'en': "",
                    'ru': "Установлена неверная валюта, пожалуйста, свяжитесь с администратором бота"
                },
                'wrong_signature': {
                    'en': "",
                    'ru':
                        "Получено уведомление об оплате, но подпись безопасности неверная."
                        " Пожалуйста, свяжитесь с администратором бота"
                },
                'wrong_currency_income': {
                    'en': "",
                    'ru':
                        "Получено уведомление об оплате, но валюты отличаются."
                        " Пожалуйста, свяжитесь с администратором бота"
                }
            }
        }
    },
    'tariffs': {
        'index': {
            'en': "",
            'ru':
                f"{emoji_codes.get('bar_chart', '')} Тарифы\n\n"
                "Внимание! При смене тарифа начисляется разница за оставшиеся дни:\n"                
                "● с положительным значением при выборе более дешёвого тарифа;\n"
                "● с отрицательным при выборе более дорогого.\n\n"
                f"{emoji_codes.get('warning_sign', '')} Однако сумма за текущий день будет списана ещё раз!"
        },
        'current': {
            'en': "",
            'ru': "<b>Ваши текущие условия</b>"
        },
        'list': {
            'wrapper': {
                'en': "",
                'ru': "{tariff_text} тариф"
            },
            0: {
                'en': "",
                'ru': "Без подписки"
            },
            1: {
                'en': "",
                'ru': emoji_codes.get('bronze_medal', '') + " Начальный"
            },
            2: {
                'en': "",
                'ru': emoji_codes.get('silver_medal', '') + " Продвинутый"
            },
            3: {
                'en': "",
                'ru': emoji_codes.get('gold_medal', '') + " Профессиональный"
            },
            4: {
                'en': "",
                'ru': emoji_codes.get('crown', '') + " Корпоративный"
            }
        },
        'info': {
            'selected': {
                'en': "",
                'ru': "(выбран)"
            }
        }
    },
    'settings': {
        'page': {
            'en': "",
            'ru': f"{emoji_codes.get('gear', '')} Настройки"
        },
        'buttons': {
            'email': {
                'en': "",
                'ru': f"{emoji_codes.get('email', '')} Почта"
            }
        },
        'email': {
            'page': {
                'en': "",
                'ru':
                    f"{emoji_codes.get('email', '')} Настройка почты\n"
                    "Текущая почта: {email}\n\n"
                    "Отправьте почту, чтобы обновить её"
            },
            'empty': {
                'en': "",
                'ru': "не установлена"
            }
        }
    },

    'navigation_builder': {
        'actions': {
            'page': {
                'en': "",
                'ru':
                    "Страница"
            },
            'of': {
                'en': "",
                'ru':
                    "из"
            },
            'back': {
                'en': "",
                'ru': "Назад"
            }
        },
        'tips': {
            'tip_send_page_num_to_go': {
                'en': "",
                'ru':
                    "Совет: отправьте номер страницы, чтобы перейти на неё"
            }
        },
        'errors': {
            'empty': {
                'en': "",
                'ru':
                    "Данных нет"
            },
            'already_on_this_page': {
                'en': "",
                'ru':
                    "Эта страница уже открыта"
            },
            'page_does_not_exist': {
                'en': "",
                'ru':
                    "Страница не существует, попробуйте перейти на первую"
            }
        }
    }
}
