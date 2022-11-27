from pkg.repository import user_repository


def register(chat_id: int, language_code: str):
    user = {"service_id": chat_id, "language_code": language_code}
    user_repository.register_or_update_by_service_id(user)
    # TODO: referral program for user.register
    # TODO: free subscription for 2 weeks


# TODO: Analytics on every income message
# def in_message(chat_id: int):
#     pass
