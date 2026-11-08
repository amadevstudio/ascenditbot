from pkg.controller.routers.stats_router import stats_router
from pkg.controller.routers.access_router import access_router
from pkg.controller.routers.bonus_channel_router import bonus_channel_router
from pkg.controller.routers.direct_messages_router import direct_messages_router
from pkg.controller.routers.group_router import group_router
from pkg.controller.routers.payment_router import payment_router
from pkg.controller.routers.quick_actions_router import quick_actions_router
from pkg.controller.routers.user_router import user_router
from pkg.controller.routers.work_router import work_router


def init_routes(dispatcher):
    # First: the channel's direct messages chat is a supergroup, the work router must not treat it as moderated
    dispatcher.include_router(direct_messages_router())

    dispatcher.include_router(payment_router())

    # Admins' commands in groups and the bot's own membership, before the moderation of group messages
    dispatcher.include_router(group_router())

    # Buttons under alerts work from any message, outside the menu's navigation
    dispatcher.include_router(quick_actions_router())
    dispatcher.include_router(access_router())

    dispatcher.include_router(stats_router())
    dispatcher.include_router(bonus_channel_router())

    dispatcher.include_router(user_router())

    dispatcher.include_router(work_router())
