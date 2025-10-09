import sqlite3
from typing import List
from models.currency import HistoricalRate


class RatesRepository:
    def __init__(self, db_path: str = "database.db") -> None:
        self.db_path: str = db_path
        self._init_db()

    def _init_db(self) -> None:
        """
        Initialize the database and create the `rates` table if it doesn't exist.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    currency TEXT NOT NULL,
                    base_currency TEXT NOT NULL,
                    date TEXT NOT NULL,
                    rate REAL NOT NULL,
                    UNIQUE(currency, base_currency, date)
                )
                """
            )
            conn.commit()

    def save_rates(
        self, currency: str, base_currency: str, rates: List[HistoricalRate]
    ) -> None:
        """
        Saves a list of exchange rates for a given currency pair into the database.
        """
        with sqlite3.connect(self.db_path) as conn:
            for rate in rates:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO historical_rates (currency, base_currency, date, rate)
                    VALUES (?, ?, ?, ?)
                    """,
                    (currency.upper(), base_currency.upper(), rate.date, rate.rate),
                )
            conn.commit()
