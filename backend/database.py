from contextlib import contextmanager
import sqlite3
from typing import Any, Iterator

import mysql.connector
from flask import current_app


class SQLiteCursor:
    def __init__(self, cursor: sqlite3.Cursor):
        self._cursor = cursor

    def execute(self, query: str, params: tuple = ()):
        self._cursor.execute(query.replace("%s", "?"), params)
        return self

    def executemany(self, query: str, params):
        self._cursor.executemany(query.replace("%s", "?"), params)
        return self

    def fetchall(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self._cursor.fetchall()]

    def fetchone(self) -> dict[str, Any] | None:
        row = self._cursor.fetchone()
        return dict(row) if row is not None else None

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self) -> None:
        self._cursor.close()


class SQLiteConnection:
    def __init__(self, database_path: str):
        self._connection = sqlite3.connect(database_path, timeout=5)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA busy_timeout = 5000")

    def cursor(self, dictionary: bool = False) -> SQLiteCursor:
        return SQLiteCursor(self._connection.cursor())

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()

    def close(self) -> None:
        self._connection.close()


def get_connection():
    if current_app.config["DB_DRIVER"] == "sqlite":
        return SQLiteConnection(current_app.config["SQLITE_PATH"])
    return mysql.connector.connect(**current_app.config["MYSQL_CONFIG"])


def is_sqlite() -> bool:
    return current_app.config["DB_DRIVER"] == "sqlite"


def fetch_all(query: str, params: tuple = ()) -> list[dict[str, Any]]:
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            cursor.close()
    finally:
        connection.close()


def fetch_one(query: str, params: tuple = ()) -> dict[str, Any] | None:
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            return cursor.fetchone()
        finally:
            cursor.close()
    finally:
        connection.close()


def execute(query: str, params: tuple = ()) -> int:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(query, params)
            connection.commit()
            return cursor.rowcount
        finally:
            cursor.close()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


@contextmanager
def transaction() -> Iterator[Any]:
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
