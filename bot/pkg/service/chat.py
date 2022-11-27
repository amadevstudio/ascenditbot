from aiogram import types
from aiogram.utils import exceptions


async def validate_bot_rights(message: types.Message, chat_id: int):
    try:
        chat_member = await message.bot.get_chat_member(chat_id, message.bot.id)
    except exceptions.Unauthorized:
        return {"error": "not_member"}

    if chat_member.status == "user":
        return {"error": "not_admin"}

    if chat_member.can_delete_messages is False:
        return {"error": "cant_edit_messages"}

    return {}


async def validate_admin_rights(message: types.Message, chat_id: int, user_id: int):
    chat_administrators = await message.bot.get_chat_administrators(chat_id)
    administrator: types.ChatMemberAdministrator | types.ChatMemberOwner | None = None

    for chat_administrator in chat_administrators:
        if chat_administrator.user.id == user_id:
            administrator = chat_administrator

    if administrator is None:
        return {"error": "user_not_admin"}

    if administrator.can_delete_messages is False:
        return {"error": "user_cant_edit_messages"}

    return {"administrator": administrator}


async def add(message: types.Message, chat_id: int, user_id: int):
    # Validate we are admin with deletion rights
    result = await validate_bot_rights(message, chat_id)
    if "error" in result:
        return {"error": result["error"]}

    # Validate client is an admin with edit rights too
    result = await validate_admin_rights(message, chat_id, user_id)
    if "error" in result:
        return {"error": result["error"]}

    administrator = result["administrator"]

    # TODO: validate administrator.status == 'creator' without premium subscription

    print(administrator)

    return {}
