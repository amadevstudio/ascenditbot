from aiogram import types


def call_and_message_accessed_processor(func):
    async def _wrap(call_or_message: types.Message | types.CallbackQuery, *args, **kwargs):
        # Call, Message, ...
        if hasattr(call_or_message, 'data'):
            await func(call_or_message, call_or_message.message, *args, **kwargs)
        else:
            await func(None, call_or_message, *args, **kwargs)

    return _wrap
