import json
from project import constants

routed_messages = {
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
  }
}
