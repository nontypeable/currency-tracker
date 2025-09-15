from litestar import get, Router


@get("/health")
async def health_check() -> str:
    return "ok"


health_check_router = Router(path="", route_handlers=[health_check])
