import sqlite3
from contextlib import contextmanager
import os

class SQLiteManager:
    """Manages SQLite database connections and transactions."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_db_schema()

    def _ensure_db_schema(self):
        """Ensures the necessary table exists in the database."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id TEXT PRIMARY KEY,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    state BLOB
                );
            """)
            conn.commit()

    @contextmanager
    def connect(self):
        """Provides a database connection, ensuring it's closed afterwards."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
