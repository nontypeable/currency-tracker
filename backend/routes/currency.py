from litestar import Router, get
from litestar.exceptions import HTTPException
from litestar.di import Provide
from litestar.status_codes import HTTP_400_BAD_REQUEST
from services.exchanges import ExchangesService
from config import get_config, Config
from models.currency import ExchangeRates
from typing import Optional
from datetime import date


async def get_exchanges_service() -> ExchangesService:
    config = get_config()
    return ExchangesService(config=config)


@get("/rates/{base_currency:str}")
async def get_rates(
    exchanges_service: ExchangesService,
    base_currency: str = "USD",
    date: Optional[date] = None,
) -> ExchangeRates:
    try:
        return await exchanges_service.get_all_currency_exchange_rates(
            base_currency=base_currency, date=date
        )
    except ValueError as e:
        raise HTTPException(detail=str(e), status_code=HTTP_400_BAD_REQUEST)
    except Exception as e:
        raise HTTPException(detail="Internal server error", status_code=500)


exchanges_router = Router(
    path="/api/currency",
    route_handlers=[get_rates],
    dependencies={"exchanges_service": Provide(get_exchanges_service)},
)
