from pkg.controller.routers.payment_router import payment_router
from pkg.controller.routers.user_router import user_router
from pkg.controller.routers.work_router import work_router


def init_routes(dispatcher):
    dispatcher.include_router(payment_router())

    dispatcher.include_router(user_router())

    dispatcher.include_router(work_router())
