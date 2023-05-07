from typing import Literal

AvailableCommands = Literal['start', 'menu', 'add_chat', 'my_chats', 'subscription']
AvailableRoutes = Literal[
    'start', 'menu', 'add_chat', 'my_chats', 'chat',
    'add_to_chat_whitelist', 'chat_whitelist', 'allowed_user',
    'subscription', 'tariffs', 'fund', 'fund_amount',
    'settings', 'settings_email',
    'nowhere']
