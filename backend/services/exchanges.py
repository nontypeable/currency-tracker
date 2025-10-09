import httpx
from xml.etree import ElementTree as ET
from typing import Optional, Dict
from datetime import date
from models.currency import ExchangeRates
import redis
from config import Config
import json
from typing import Dict
from repositories.rates_repository import RatesRepository
from typing import List
from models import HistoricalRate


class ExchangesService:
    def __init__(
        self, config: Config, redis_client: Optional[redis.Redis] = None
    ) -> None:
        self._base_url = "http://www.cbr.ru/scripts/XML_daily.asp"
        self.config = config
        self.redis_client = redis_client or self._create_redis_client()
        self.repository = RatesRepository()

    def _create_redis_client(self) -> redis.Redis:
        return redis.Redis(
            host=self.config.redis_host,
            port=self.config.redis_port,
            db=self.config.redis_db,
            decode_responses=True,
            socket_timeout=5,
        )
    
    async def get_historical_rates(
        self, currency: str, base_currency: str, days: int = 30
    ) -> List[HistoricalRate]:
        """
        Get historical exchange rates with database caching.
        """
        cache_key = f"historical:{currency}:{base_currency}:{days}"

        if self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return [HistoricalRate(**item) for item in json.loads(cached_data)]
            except redis.RedisError:
                pass

        db_rates = self.repository.get_rates(currency, base_currency, days)
        if db_rates:
            if self.redis_client:
                try:
                    self.redis_client.setex(
                        cache_key,
                        3600,
                        json.dumps(
                            [{"date": r.date, "rate": r.rate} for r in db_rates]
                        ),
                    )
                except redis.RedisError:
                    pass
            return db_rates 

        missing_dates = self.repository.get_missing_dates(currency, base_currency, days)
        rates_to_save = []

        for missing_date in missing_dates:
            try:
                if base_currency == "RUB":
                    rate = await self.get_currency_exchange_rate(currency, missing_date)
                    historical_rate = HistoricalRate(
                        date=missing_date.isoformat(), rate=rate
                    )
                else:
                    currency_to_rub = await self.get_currency_exchange_rate(
                        currency, missing_date
                    )
                    base_to_rub = await self.get_currency_exchange_rate(
                        base_currency, missing_date
                    )
                    cross_rate = currency_to_rub / base_to_rub
                    historical_rate = HistoricalRate(
                        date=missing_date.isoformat(), rate=cross_rate
                    )

                rates_to_save.append(historical_rate)

            except Exception as e:
                continue

        if rates_to_save:
            self.repository.save_rates(currency, base_currency, rates_to_save)

        final_rates = self.repository.get_rates(currency, base_currency, days)
        if final_rates:
            if self.redis_client:
                try:
                    self.redis_client.setex(
                        cache_key,
                        3600,
                        json.dumps(
                            [{"date": r.date, "rate": r.rate} for r in final_rates]
                        ),
                    )
                except redis.RedisError:
                    pass
            return final_rates

        return []
    
    async def update_daily_rates(self) -> None:
        """
        Update database with today's rates for all available currencies.
        """
        try:
            exchange_rates = await self.get_all_currency_exchange_rates("RUB")
            today = date.today()

            for currency, rate in exchange_rates.rates.items():
                if currency != "RUB":
                    historical_rate = HistoricalRate(date=today.isoformat(), rate=rate)
                    self.repository.save_single_rate(currency, "RUB", historical_rate)

        except Exception as e:
            pass

    async def get_all_available_currencies(self) -> List[str]:
        """
        Get list of all available currency codes from CBR.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self._base_url)
                response.raise_for_status()
                root = ET.fromstring(response.content)

                currencies = []
                for valute in root.findall("Valute"):
                    char_code = valute.findtext("CharCode")
                    if char_code:
                        currencies.append(char_code)

                currencies.append("RUB")
                return sorted(list(set(currencies)))
        except Exception as e:
            return [
                "USD",
                "EUR",
                "GBP",
                "JPY",
                "CNY",
                "CHF",
                "CAD",
                "AUD",
                "KRW",
                "RUB",
            ]
        
    async def get_currency_exchange_rate(
        self, char_code: str, date: Optional[date] = None
    ) -> float:
        """
        Get exchange rate for a specific currency to RUB.
        """
        cache_key = f"rate:{char_code.upper()}:{date.isoformat() if date else 'latest'}"

        if self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data and isinstance(cached_data, str):
                    return float(cached_data)
            except redis.RedisError:
                pass

        async with httpx.AsyncClient() as client:
            response = await self._make_request(client, date)
            currency_rate = self._parse_currency_rate(response.content, char_code)

            if self.redis_client:
                try:
                    self.redis_client.setex(
                        cache_key, 3600, str(currency_rate)  # ttl 1 hour
                    )
                except redis.RedisError:
                    pass

            return currency_rate

    async def get_all_currency_exchange_rates(
        self, base_currency: str, date: Optional[date] = None
    ) -> ExchangeRates:
        cache_key = (
            f"rates_all:{base_currency}:{date.isoformat() if date else 'latest'}"
        )

        if self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data and isinstance(cached_data, str):
                    data = json.loads(cached_data)
                    return ExchangeRates(**data)
            except (redis.RedisError, json.JSONDecodeError):
                pass

        params = self._build_request_params(date)
        async with httpx.AsyncClient() as client:
            response = await client.get(self._base_url, params=params)
            exchange_rates = self._parse_exchange_rates(response.content, base_currency)

            if self.redis_client:
                try:
                    serialized_data = json.dumps(
                        {
                            "base": exchange_rates.base,
                            "rates": exchange_rates.rates,
                            "last_updated": exchange_rates.last_updated,
                        }
                    )

                    self.redis_client.setex(
                        cache_key, 3600, serialized_data  # ttl 1 hour
                    )
                except redis.RedisError:
                    pass

            return exchange_rates

    def _build_request_params(self, date: Optional[date]) -> Dict[str, str]:
        return {"date_req": date.strftime("%d.%m.%Y")} if date else {}

    async def _make_request(
        self, client: httpx.AsyncClient, date: Optional[date]
    ) -> httpx.Response:
        """Make HTTP request to get exchange rates."""
        params = self._build_request_params(date)
        response = await client.get(self._base_url, params=params)
        response.raise_for_status()
        return response

    def _parse_currency_rate(self, xml_content: bytes, char_code: str) -> float:
        """Parse XML content to extract specific currency rate."""
        root = ET.fromstring(xml_content)
        target_code = char_code.upper()

        for valute in root.findall("Valute"):
            code_element = valute.find("CharCode")
            if code_element is not None and code_element.text == target_code:
                value_element = valute.find("Value")
                nominal_element = valute.find("Nominal")
                if value_element is not None and nominal_element is not None:
                    value_text = value_element.text
                    nominal_text = nominal_element.text
                    if value_text is not None and nominal_text is not None:
                        try:
                            value_float = float(value_text.replace(",", "."))
                            nominal_int = int(nominal_text)
                            return value_float / nominal_int
                        except (ValueError, TypeError):
                            continue
        raise ValueError(f"Currency {char_code} not found")

    def _parse_exchange_rates(
        self, xml_content: bytes, base_currency: str
    ) -> ExchangeRates:
        root = ET.fromstring(xml_content)
        rates_to_rub = self._extract_rates_to_rub(root)

        if base_currency == "RUB":
            exchange_rates = self._calculate_rub_base_rates(rates_to_rub)
        else:
            exchange_rates = self._calculate_cross_rates(rates_to_rub, base_currency)

        return ExchangeRates(
            base=base_currency,
            rates=exchange_rates,
            last_updated=root.attrib.get("Date", ""),
        )

    def _extract_rates_to_rub(self, root: ET.Element) -> Dict[str, float]:
        rates = {}
        for valute in root.findall("Valute"):
            char_code = valute.findtext("CharCode")
            value = valute.findtext("Value")
            nominal = valute.findtext("Nominal")

            if char_code is None or value is None or nominal is None:
                continue

            try:
                rate = float(value.replace(",", ".")) / float(nominal)
                rates[char_code] = rate
            except (ValueError, TypeError):
                continue

        rates["RUB"] = 1.0
        return rates

    def _calculate_rub_base_rates(self, rates: Dict[str, float]) -> Dict[str, float]:
        return {currency: 1 / rate for currency, rate in rates.items()}

    def _calculate_cross_rates(
        self, rates_to_rub: Dict[str, float], base_currency: str
    ) -> Dict[str, float]:
        if base_currency not in rates_to_rub:
            raise ValueError(f"Base currency {base_currency} not found")

        base_rate = rates_to_rub[base_currency]
        return {currency: base_rate / rate for currency, rate in rates_to_rub.items()}
