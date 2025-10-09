import sqlite3


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
