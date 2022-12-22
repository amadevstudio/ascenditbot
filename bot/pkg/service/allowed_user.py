import datetime

allowed_user_interface = {
    'id': int,
    'moderated_chat_id': int,
    'nickname': str,
    'active': bool,
    'images_allowed': bool,
    'links_allowed': bool,
    'period_quantity': int,
    'period_type': str,
    'period_quantity_left': int,
    'ban_expiration_date': datetime.datetime,
    'created_at': datetime.datetime,
    'updated_at': datetime.datetime
}


class AllowedUser:
    @classmethod
    def find(user_id: int):
        pass
