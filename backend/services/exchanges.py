import httpx
from xml.etree import ElementTree as ET
from typing import Optional, Dict
from datetime import date
from models.currency import ExchangeRates


class ExchangesService:
    def __init__(self) -> None:
        self._base_url = "http://www.cbr.ru/scripts/XML_daily.asp"

    async def get_currency_exchange_rate(
        self, char_code: str, date: Optional[date] = None
    ) -> float:
        """
        Get exchange rate for a specific currency to RUB.
        """
        async with httpx.AsyncClient() as client:
            response = await self._make_request(client, date)
            return self._parse_currency_rate(response.content, char_code)

    async def get_all_currency_exchange_rates(
        self, base_currency: str, date: Optional[date] = None
    ) -> ExchangeRates:
        params = self._build_request_params(date)
        async with httpx.AsyncClient() as client:
            response = await client.get(self._base_url, params=params)
            response.raise_for_status()
            return self._parse_exchange_rates(response.content, base_currency)

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
