import sqlite3
from typing import List, Optional
from datetime import date, timedelta
from models.currency import HistoricalRate


class RatesRepository:
    def __init__(self, db_path: str = "database.db") -> None:
        self.db_path: str = db_path
        self._init_db()

    def _init_db(self) -> None:
        """
        Initialize the database and create the `historical_rates` table if it doesn't exist.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS historical_rates (
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

    def get_rate_by_date(
        self, currency: str, base_currency: str, target_date: date
    ) -> Optional[HistoricalRate]:
        """
        Gets the exchange rate for a given currency pair on a specific date.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                    SELECT date, rate FROM historical_rates
                    WHERE currency = ? AND base_currency = ? AND date = ?
                    """,
                (currency.upper(), base_currency.upper(), target_date.isoformat()),
            )
            row = cursor.fetchone()
            if row:
                return HistoricalRate(date=row[0], rate=row[1])
            return None

    def save_single_rate(
        self, currency: str, base_currency: str, rate: HistoricalRate
    ) -> None:
        """
        Saves a single exchange rate into the database.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO historical_rates (currency, base_currency, date, rate)
                VALUES (?, ?, ?, ?)
                """,
                (currency.upper(), base_currency.upper(), rate.date, rate.rate),
            )
            conn.commit()

    def get_rates(
        self, currency: str, base_currency: str, days: int
    ) -> Optional[List[HistoricalRate]]:
        """
        Gets historical exchange rates for a given currency pair from the database.
        """
        today = date.today()
        start_date = today - timedelta(days=days - 1)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT date, rate FROM historical_rates
                WHERE currency = ? AND base_currency = ? AND date >= ?
                ORDER BY date ASC
                """,
                (currency.upper(), base_currency.upper(), start_date.isoformat()),
            )
            rows = cursor.fetchall()
            if len(rows) >= days:
                return [HistoricalRate(date=row[0], rate=row[1]) for row in rows]
            return None

    def get_latest_rate(
        self, currency: str, base_currency: str
    ) -> Optional[HistoricalRate]:
        """
        Gets the latest exchange rate for a given currency pair.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT date, rate FROM historical_rates
                WHERE currency = ? AND base_currency = ?
                ORDER BY date DESC
                LIMIT 1
                """,
                (currency.upper(), base_currency.upper()),
            )
            row = cursor.fetchone()
            if row:
                return HistoricalRate(date=row[0], rate=row[1])
            return None

    def get_missing_dates(
        self, currency: str, base_currency: str, days: int
    ) -> List[date]:
        """
        Returns list of dates for which we don't have data in the specified period.
        """
        today = date.today()
        start_date = today - timedelta(days=days - 1)

        all_dates = []
        current_date = start_date
        while current_date <= today:
            all_dates.append(current_date)
            current_date += timedelta(days=1)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT DISTINCT date FROM historical_rates
                WHERE currency = ? AND base_currency = ? AND date >= ?
                """,
                (currency.upper(), base_currency.upper(), start_date.isoformat()),
            )
            existing_dates = [date.fromisoformat(row[0]) for row in cursor.fetchall()]

        return [d for d in all_dates if d not in existing_dates]

    def get_missing_dates_for_range(
        self, currency: str, base_currency: str, start_date: date, end_date: date
    ) -> List[date]:
        """
        Returns list of dates for which we don't have data in the specified date range.
        """
        all_dates = []
        current_date = start_date
        while current_date <= end_date:
            all_dates.append(current_date)
            current_date += timedelta(days=1)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT DISTINCT date FROM historical_rates
                WHERE currency = ? AND base_currency = ? AND date >= ? AND date <= ?
                """,
                (
                    currency.upper(),
                    base_currency.upper(),
                    start_date.isoformat(),
                    end_date.isoformat(),
                ),
            )
            existing_dates = [date.fromisoformat(row[0]) for row in cursor.fetchall()]

        return [d for d in all_dates if d not in existing_dates]