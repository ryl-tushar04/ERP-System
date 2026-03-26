from typing import Any

from psycopg2 import pool
from psycopg2.extensions import connection as PsycopgConnection
from psycopg2.extras import RealDictCursor

from .core.config import settings
from .core.database import Base, SessionLocal, engine, get_db

_connection_pool: pool.ThreadedConnectionPool | None = None


def get_connection_pool() -> pool.ThreadedConnectionPool:
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = pool.ThreadedConnectionPool(
            minconn=settings.postgres_pool_min_size,
            maxconn=settings.postgres_pool_max_size,
            host=settings.postgres_host,
            port=settings.postgres_port,
            dbname=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
        )
    return _connection_pool


def _release_connection(
    connection_pool: pool.ThreadedConnectionPool,
    connection: PsycopgConnection,
    discard: bool = False,
) -> None:
    connection_pool.putconn(connection, close=discard)


def execute_select_query(
    query: str,
    params: tuple[Any, ...] | None = None,
) -> list[dict[str, Any]]:
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("SQL query must not be empty.")

    if not normalized_query.lower().startswith(("select", "with")):
        raise ValueError("Only SELECT queries are allowed.")

    connection_pool = get_connection_pool()
    connection = connection_pool.getconn()

    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(normalized_query, params)
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
    except Exception:
        connection.rollback()
        _release_connection(connection_pool, connection, discard=True)
        raise
    else:
        connection.rollback()
        _release_connection(connection_pool, connection)
        return result


def close_connection_pool() -> None:
    global _connection_pool
    if _connection_pool is not None:
        _connection_pool.closeall()
        _connection_pool = None


__all__ = [
    "Base",
    "SessionLocal",
    "engine",
    "get_db",
    "get_connection_pool",
    "close_connection_pool",
    "execute_select_query",
]
