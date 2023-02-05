from aiogram import types


def call_and_message_accessed_processor(call_or_message: types.Message | types.CallbackQuery) \
        -> [types.CallbackQuery | None, types.Message]:
    # Call, Message, ...
    if hasattr(call_or_message, 'data'):
        return call_or_message, call_or_message.message
    else:
        return None, call_or_message
