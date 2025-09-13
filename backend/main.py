from litestar import Litestar
from routes import currency

app = Litestar(
    route_handlers=[currency.exchanges_router],
)
