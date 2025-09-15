from litestar import Litestar
from litestar.config.cors import CORSConfig
from routes import currency
from routes import healthcheck


app = Litestar(
    route_handlers=[currency.exchanges_router, healthcheck.health_check_router],
    cors_config=CORSConfig(
        allow_origins=["http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    ),
)
