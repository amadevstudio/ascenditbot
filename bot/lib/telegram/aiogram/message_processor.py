from framework.system import telegram_types


def call_and_message_accessed_processor(call_or_message: telegram_types.Message | telegram_types.CallbackQuery) \
        -> [telegram_types.CallbackQuery | None, telegram_types.Message]:
    # Call, Message, ...
    if hasattr(call_or_message, 'data'):
        return call_or_message, call_or_message.message
    else:
        return None, call_or_message
