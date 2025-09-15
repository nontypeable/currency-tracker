from litestar import Litestar
from routes import currency
from routes import healthcheck

app = Litestar(
    route_handlers=[currency.exchanges_router, healthcheck.health_check_router],
)
