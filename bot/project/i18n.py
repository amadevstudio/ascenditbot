import json
from project import constants

emoji_codes = {
    'new': '🆕',  # \U0001F195
    'group': '👥',
    'sos': '🆘',
    'credit_card': '💳',
    'down_arrow': '⬇️'
}

routed_messages = {
    "buttons": {
        "back": {
            "en": "",
            "ru": "Назад"
        },
        "my_groups": {
            "en": "",
            "ru": f"{emoji_codes.get('group', '')} Мои группы"
        },
        "add_group": {
            "en": "",
            "ru": f"{emoji_codes.get('new', '')} Добавить группу"
        },
        "help": {
            "en": "",
            "ru": f"{emoji_codes.get('sos', '')} Помощь"
        },
        "payment": {
            "en": "",
            "ru": f"{emoji_codes.get('credit_card', '')} Оплата"
        }
    },
    "welcome": {
        "introduction": {
            "en": "",
            "ru":
                "Добро пожаловать! Этот бот позволяет создавать белые списки для групп, а в будущем научится ещё "
                "множеству полезных вещей.\n\n"
                "Экономьте время с помощью @{bot_name}!"
                .format(bot_name=constants.bot_name.lower())
        },
        "let's begin": {
            "en": "",
            "ru":
                "Начнём!"
        }
    },
    "menu": {
        "text": {
            "en": "",
            "ru": "Меню"
        }
    },
    "add_group": {
        "instruction": {
            "en": "",
            "ru":
                "Чтобы добавить группу в бота, следуйте простым шагам:\n\n"
                "1. Сделайте бота администратором вашей группы с возможностью редактирования сообщений;\n"
                "2. Находясь в этом меню, перешлите боту любое сообщение из группы."
                f"{emoji_codes.get('down_arrow', '') * 3}\n\n"
                "Группа добавится, если вы есть в списках администраторов с возможностью редактирования сообщений."
        }
    }
}
