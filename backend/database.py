from contextlib import contextmanager
from typing import Any, Iterator

import mysql.connector
from flask import current_app


def get_connection():
    return mysql.connector.connect(**current_app.config["MYSQL_CONFIG"])


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
