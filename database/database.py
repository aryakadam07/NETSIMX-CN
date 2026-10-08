"""
NetSimX — SQLite Database Connection Manager (Member 4)
Thread-safe SQLite access with WAL mode and connection-per-call pattern.
"""

import sqlite3
import threading
import logging
from pathlib import Path
from typing import Optional
from .schema import SCHEMA_SQL

logger = logging.getLogger("Database")


class Database:
    """
    Central SQLite database manager.
    Uses thread-local connections to be safe when called from QThread workers.
    """

    def __init__(self, db_path: str):
        self.db_path = str(db_path)
        self._local = threading.local()
        self._initialized = False

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Creates all tables and sets WAL mode. Must be called once at startup."""
        conn = self._connect()
        try:
            conn.executescript(SCHEMA_SQL)
            conn.commit()
            self._initialized = True
            logger.info(f"Database initialized at {self.db_path}")
        except sqlite3.Error as exc:
            logger.error(f"Database initialization failed: {exc}")
            raise

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Returns the thread-local connection, creating it if needed."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA foreign_keys = ON;")
            self._local.conn = conn
        return self._local.conn

    def get_connection(self) -> sqlite3.Connection:
        """Public accessor for a thread-local connection."""
        return self._connect()

    def close(self) -> None:
        """Closes the current thread's connection."""
        if hasattr(self._local, "conn") and self._local.conn:
            try:
                self._local.conn.close()
            except Exception:
                pass
            self._local.conn = None

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        conn = self._connect()
        return conn.execute(sql, params)

    def executemany(self, sql: str, params_list) -> None:
        conn = self._connect()
        conn.executemany(sql, params_list)

    def commit(self) -> None:
        conn = self._connect()
        conn.commit()

    def fetchall(self, sql: str, params: tuple = ()):
        cursor = self.execute(sql, params)
        return cursor.fetchall()

    def fetchone(self, sql: str, params: tuple = ()):
        cursor = self.execute(sql, params)
        return cursor.fetchone()
