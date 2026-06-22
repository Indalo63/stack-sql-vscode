"""
Conexión a PostgreSQL con pool de conexiones (ThreadedConnectionPool).
El pool se crea en el primer uso para no fallar en tiempo de importación
si Docker no está levantado.
"""

from contextlib import contextmanager
import psycopg2
from psycopg2 import pool as pg_pool
from app.config import DB_CONFIG

_pool: pg_pool.ThreadedConnectionPool | None = None


def _get_pool() -> pg_pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        _pool = pg_pool.ThreadedConnectionPool(minconn=1, maxconn=5, **DB_CONFIG)
    return _pool


@contextmanager
def get_connection():
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)
