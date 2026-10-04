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
            # The id column should not be PRIMARY KEY if we want to store multiple checkpoints
            # for the same agent and retrieve the latest one.
            # PRIMARY KEY implies uniqueness. We need (id, timestamp) to be unique, or just
            # allow multiple entries for 'id' and query by timestamp.
            # For simplicity and to allow retrieving the *latest* state by ID, we'll
            # remove PRIMARY KEY from 'id' and potentially add an index for faster lookups.
            # However, for 'INSERT OR REPLACE' to work as intended (updating the latest state),
            # 'id' needs to be unique.
            # The current 'INSERT OR REPLACE INTO checkpoints (id, timestamp, state) VALUES (?, ?, ?)'
            # will replace based on 'id' being the PRIMARY KEY. This means only one entry per agent ID.
            # If the intent is to have a history of checkpoints, then 'id' should not be PRIMARY KEY.
            # Let's adjust the schema to allow multiple checkpoints per agent, with a proper primary key
            # and an index on agent ID for efficient lookup of the latest state.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    pk_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    state BLOB,
                    UNIQUE(id, timestamp) -- Ensure no duplicate checkpoints for the same agent at the exact same timestamp
                );
            """)
            # Add an index on 'id' for faster lookup of checkpoints for a specific agent
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_id ON checkpoints (id);")
            conn.commit()

    @contextmanager
    def connect(self):
        """Provides a database connection, ensuring it's closed afterwards."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
