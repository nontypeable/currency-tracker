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


@get("/historical/{currency:str}/{base_currency:str}/{days:int}")
async def get_historical_rates(
    exchanges_service: ExchangesService,
    currency: str,
    base_currency: str,
    days: int = 30,
) -> list:
    """Get historical exchange rates"""
    try:
        rates = await exchanges_service.get_historical_rates(
            currency, base_currency, days
        )
        return [{"date": r.date, "rate": r.rate} for r in rates]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


exchanges_router = Router(
    path="/api/currency",
    route_handlers=[get_rates, get_historical_rates],
    dependencies={"exchanges_service": Provide(get_exchanges_service)},
)


@post("/update-rates")
async def update_rates(exchanges_service: ExchangesService) -> Dict[str, str]:
    """Update database with latest rates"""
    try:
        await exchanges_service.update_daily_rates()
        return {"status": "success", "message": "Rates updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@post("/preload-data/{days:int}")
async def preload_historical_data(
    exchanges_service: ExchangesService,
    days: int = 180,
) -> Dict[str, str]:
    """Manually trigger historical data preload"""
    try:
        await exchanges_service.preload_historical_data(days=days)
        return {
            "status": "success",
            "message": f"Preloaded {days} days of historical data",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@get("/currencies")
async def get_available_currencies(
    exchanges_service: ExchangesService,
) -> Dict[str, list]:
    """Get list of all available currencies"""
    try:
        currencies = await exchanges_service.get_all_available_currencies()
        return {"currencies": currencies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

