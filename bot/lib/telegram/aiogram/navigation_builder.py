import json
import math
from typing import Callable

from aiogram import types

from lib.python.singleton import Singleton


class NavigationBuilder(metaclass=Singleton):
    def __init__(
            self, messages_getter: Callable = None, base_messages_domain: list = None, back_button_data: str = None
    ):
        if base_messages_domain is None:
            base_messages_domain = []

        if back_button_data is None:
            back_button_data = json.dumps({'tp': 'back'})

        self.messages_getter = messages_getter
        self.base_messages_domain = base_messages_domain
        self.back_button_data = back_button_data

    def get_message(self, route, language_code):
        return self.messages_getter(self.base_messages_domain + route, language_code)

    # возвращает текущую страницу
    @staticmethod
    def get_state_page(call: types.CallbackQuery | None, message: types.Message, state_data):
        try:
            if call is not None:
                try:
                    p = json.loads(call.data)["p"]
                except KeyError:
                    # не удалось получить канал из кнопки — берём из состояния
                    p = state_data["p"]
            else:
                p = int(message.text)
                if p < 1:
                    p = 1

        except Exception:
            p = 1

        return p

    # возвращает данные из бд на нужной странице и общее количество
    @staticmethod
    def load_page_data(
            data_provider: Callable, data_params: list, data_count_provider: Callable, data_count_params: list,
            curr_page: int, per_page: int, order_field: str):

        if curr_page < 1:
            curr_page = 1

        count = data_count_provider(*data_count_params)

        if count == 0:
            return {
                "error": "empty"
            }

        page_count = math.ceil(count / per_page)
        if curr_page > page_count:
            curr_page = page_count

        offset = per_page * (curr_page - 1)

        data = data_provider(*data_params, order_field, per_page, offset)

        return {
            'data': data,
            'page_count': page_count,
            'curr_page': curr_page
        }

    # возвращает кнопки переключения страниц
    def generate_nav_layout(self, curr_page, page_count, curr_type, language_code, back_button_text="back"):
        buttons = []

        cb_data = {"tp": curr_type, "p": curr_page - 1}
        text = ("❮" if curr_page > 1 else "-")
        button_prev = types.InlineKeyboardButton(
            text=text, callback_data=json.dumps(cb_data))
        buttons.append(button_prev)

        b = types.InlineKeyboardButton(
            text=self.get_message(["actions", back_button_text], language_code), callback_data=self.back_button_data)
        buttons.append(b)

        text = ("❯" if curr_page < page_count else "-")
        cb_data = {"tp": curr_type, "p": curr_page + 1}
        button_next = types.InlineKeyboardButton(
            text=text, callback_data=json.dumps(cb_data))
        buttons.append(button_next)

        return buttons

    # возвращает сообщение "x страница из y"
    def _get_page_of_pages(self, curr_page, page_count, language_code):
        return str(curr_page) + " " \
               + self.get_message(["actions", "page"], language_code).lower() + " " \
               + self.get_message(["actions", "of"], language_code).lower() + " " + str(page_count)

    def get_routing_helper_message(
            self, curr_page, page_count, language_code, with_tip=True, divider=None
    ):
        if page_count == 1:
            return ""

        else:
            result = "\n" + self._get_page_of_pages(curr_page, page_count, language_code)
            if with_tip:
                result += "\n\n" + self.get_message(["tips", "tip_send_page_num_to_go"], language_code)
            if divider is not None:
                result = divider + result
            return result

    def full_message_setup(self, call, message, state_data, current_type, language_code,
                           data_provider, data_params, data_count_provider, data_count_params, per_page, order_field):
        current_page = self.__class__.get_state_page(call, message, state_data)
        user_chat_page_data = self.__class__.load_page_data(
            data_provider, data_params, data_count_provider, data_count_params, current_page, per_page, order_field)
        if "error" in user_chat_page_data:
            return current_page, user_chat_page_data, None, None

        current_page = user_chat_page_data['curr_page']

        routing_helper_message = self.get_routing_helper_message(
            current_page, user_chat_page_data['page_count'], language_code)
        nav_layout = self.generate_nav_layout(
            current_page, user_chat_page_data['page_count'], current_type, language_code)

        return current_page, user_chat_page_data, routing_helper_message, nav_layout
