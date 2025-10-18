from litestar import Litestar
from litestar.config.cors import CORSConfig
from routes import currency
from routes import healthcheck
from repositories.rates_repository import RatesRepository
from services.exchanges import ExchangesService
from config import get_config
from loguru import logger
import asyncio
import threading


# Initialize database on startup
def init_db():
    """
    Initialize database tables.
    """
    repo = RatesRepository()
    logger.info("Database initialized successfully")


async def preload_data():
    """
    Preload historical data in background.
    """

    logger.info("Starting background historical data preload...")

    try:
        config = get_config()
        exchange_service = ExchangesService(config=config)

        await exchange_service.preload_historical_data(days=180)
        logger.info("Background data preload completed successfully!")

    except Exception as e:
        logger.error(f"Background data preload failed: {e}")


def start_background_preload():
    """
    Start background preload task.
    """

    def run_preload():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(preload_data())
        except Exception as e:
            logger.error(f"Background preload thread failed: {e}")
        finally:
            loop.close()

    thread = threading.Thread(target=run_preload, daemon=True)
    thread.start()
    logger.info("Background preload thread started")


app = Litestar(
    route_handlers=[currency.exchanges_router, healthcheck.health_check_router],
    cors_config=CORSConfig(
        allow_origins=["http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    ),
    on_startup=[init_db, start_background_preload],
)