from typing import Literal

AvailableCommands = Literal['start', 'menu', 'add_chat', 'my_chats', 'subscription']
AvailableRoutes = Literal[
    'start', 'privacy', 'help', 'menu', 'add_chat', 'my_chats', 'chat',
    'add_to_chat_whitelist', 'chat_whitelist', 'allowed_user', 'chat_restriction_duration',
    'subscription', 'tariffs', 'fund', 'fund_currency', 'fund_amount',
    'settings', 'settings_email', 'settings_currency',
    'nowhere']
