from dataclasses import dataclass
from typing import Dict


@dataclass
class ExchangeRates:
    base: str
    rates: Dict[str, float]
    last_updated: str
