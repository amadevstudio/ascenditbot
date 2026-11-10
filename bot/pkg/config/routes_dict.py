from typing import Literal

AvailableCommands = Literal['start', 'menu', 'add_chat', 'my_chats', 'subscription', 'bonus']
AvailableRoutes = Literal[
    'start', 'privacy', 'help', 'menu', 'add_chat', 'my_chats', 'chat',
    'add_to_chat_whitelist', 'chat_whitelist', 'allowed_user', 'chat_restriction_duration', 'chat_access',
    'chat_post_limit', 'chat_topics',
    'subscription', 'tariffs', 'fund', 'fund_currency', 'fund_amount',
    'settings', 'settings_email', 'settings_currency', 'bonus',
    'admin', 'admin_bot', 'admin_sources', 'admin_source', 'admin_add_source', 'admin_channels', 'admin_add_channel',
    'nowhere']
