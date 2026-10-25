"""
Database Access and Connection Manager for Internal Marks Management System.
Supports both psycopg2 and psycopg3 drivers with automatic fallback,
dictionary cursor support, transaction control, and user-friendly error formatting.
"""

import sys
from contextlib import contextmanager
from typing import Generator, Any, Optional, Dict, List, Tuple
from config import get_current_config, DatabaseConfig

# Try importing PostgreSQL drivers
DRIVER_NAME = None
psycopg_driver = None
psycopg2_driver = None
DictCursorFactory = None

try:
    import psycopg2
    import psycopg2.extras
    psycopg2_driver = psycopg2
    DRIVER_NAME = "psycopg2"
    DictCursorFactory = psycopg2.extras.RealDictCursor
except ImportError:
    try:
        import psycopg
        from psycopg.rows import dict_row
        psycopg_driver = psycopg
        DRIVER_NAME = "psycopg3"
    except ImportError:
        DRIVER_NAME = None


class DatabaseError(Exception):
    """Base exception for application database errors."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when connecting to PostgreSQL fails."""
    pass


class DatabaseIntegrityError(DatabaseError):
    """Raised when a unique, check, foreign key, or trigger constraint fails."""
    pass


def get_driver_name() -> Optional[str]:
    """Return the name of the active PostgreSQL driver."""
    return DRIVER_NAME


import time

_LAST_FAILURE_TIME = 0.0
_LAST_FAILURE_MSG = ""


def reset_connection_cache():
    """Clear cached connection failure to allow an immediate fresh connection attempt."""
    global _LAST_FAILURE_TIME, _LAST_FAILURE_MSG
    _LAST_FAILURE_TIME = 0.0
    _LAST_FAILURE_MSG = ""


def create_raw_connection(cfg: Optional[DatabaseConfig] = None, force_retry: bool = False):
    """Establish and return a new raw database connection with fast-fail caching."""
    global _LAST_FAILURE_TIME, _LAST_FAILURE_MSG

    if DRIVER_NAME is None:
        raise DatabaseConnectionError(
            "No PostgreSQL driver found. Please install psycopg2-binary or psycopg:\n"
            "pip install psycopg2-binary"
        )

    # Fast-fail if recent connection attempt failed within the last 3 seconds
    now = time.time()
    if not force_retry and (now - _LAST_FAILURE_TIME) < 3.0:
        raise DatabaseConnectionError(_LAST_FAILURE_MSG)

    if cfg is None:
        cfg = get_current_config()

    try:
        if DRIVER_NAME == "psycopg2":
            conn = psycopg2_driver.connect(
                host=cfg.host,
                port=cfg.port,
                dbname=cfg.database,
                user=cfg.user,
                password=cfg.password,
                connect_timeout=2
            )
            _LAST_FAILURE_TIME = 0.0
            return conn
        else:
            conn = psycopg_driver.connect(
                host=cfg.host,
                port=cfg.port,
                dbname=cfg.database,
                user=cfg.user,
                password=cfg.password,
                connect_timeout=2
            )
            _LAST_FAILURE_TIME = 0.0
            return conn
    except Exception as e:
        err_msg = str(e).strip()
        if "password authentication failed" in err_msg.lower():
            friendly = f"Authentication failed for user '{cfg.user}'. Please check DB_PASSWORD in .env."
        elif "connection refused" in err_msg.lower() or "could not connect to server" in err_msg.lower():
            friendly = f"Could not connect to PostgreSQL server at {cfg.host}:{cfg.port}. Is PostgreSQL service running?"
        elif f'database "{cfg.database}" does not exist' in err_msg.lower():
            friendly = f"Database '{cfg.database}' does not exist. Please create it in pgAdmin or run 'CREATE DATABASE {cfg.database};'."
        else:
            friendly = f"Database connection error: {err_msg}"

        _LAST_FAILURE_TIME = time.time()
        _LAST_FAILURE_MSG = friendly
        raise DatabaseConnectionError(friendly) from e


def test_connection(cfg: Optional[DatabaseConfig] = None) -> Tuple[bool, str]:
    """
    Test connectivity to the PostgreSQL database.
    Returns (True, "Connected successfully") or (False, error_message).
    """
    try:
        conn = create_raw_connection(cfg, force_retry=True)
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                v = cur.fetchone()
                version_str = v[0] if isinstance(v, (list, tuple)) else str(v)
                short_ver = version_str.split(",")[0] if version_str else "PostgreSQL"
                return True, f"Successfully connected to {short_ver} ({DRIVER_NAME})"
        finally:
            conn.close()
    except Exception as e:
        return False, str(e)


@contextmanager
def get_db_cursor(commit: bool = True) -> Generator[Any, None, None]:
    """
    Context manager that yields a dictionary-like cursor.
    Commits on successful completion if commit=True, and rolls back on exception.
    Always cleans up cursor and connection.
    """
    conn = create_raw_connection()
    cur = None
    try:
        if DRIVER_NAME == "psycopg2":
            cur = conn.cursor(cursor_factory=DictCursorFactory)
        else:
            from psycopg.rows import dict_row
            cur = conn.cursor(row_factory=dict_row)

        yield cur

        if commit:
            conn.commit()
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        # Translate error into user-friendly integrity or db error
        err_str = str(e)
        if "unique constraint" in err_str.lower():
            if "uq_student_roll" in err_str:
                raise DatabaseIntegrityError("A student with this Roll Number already exists in the same Class and Division.")
            elif "uq_student_subject" in err_str:
                raise DatabaseIntegrityError("A marks record for this student and subject already exists.")
            elif "subject_subject_name_key" in err_str:
                raise DatabaseIntegrityError("A subject with this name already exists.")
            raise DatabaseIntegrityError(f"Duplicate record violation: {err_str}")
        elif "violates foreign key constraint" in err_str.lower():
            if "fk_marks_student" in err_str:
                raise DatabaseIntegrityError("Cannot delete or update student because associated marks records exist. Remove student marks first.")
            elif "fk_marks_subject" in err_str:
                raise DatabaseIntegrityError("Cannot delete or update subject because associated marks records exist. Remove subject marks first.")
            raise DatabaseIntegrityError(f"Foreign key constraint violation: {err_str}")
        elif "violates check constraint" in err_str.lower():
            raise DatabaseIntegrityError(f"Data value violates check constraint: {err_str}")
        elif "exceeds maximum marks" in err_str.lower() or "cannot reduce max_marks" in err_str.lower():
            # Trigger raised exception
            raise DatabaseIntegrityError(err_str)
        raise DatabaseError(err_str) from e
    finally:
        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass
        try:
            conn.close()
        except Exception:
            pass


def execute_query(
    sql: str,
    params: Optional[Tuple[Any, ...]] = None,
    fetch: Optional[str] = None,
    commit: Optional[bool] = None
) -> Any:
    """
    Execute a parameterized SQL query safely.
    :param sql: Parameterized SQL string using %s placeholders
    :param params: Tuple of parameters
    :param fetch: 'all' to fetch all rows as dicts, 'one' to fetch single row, None for DML execution
    :param commit: If True, commits the transaction. Defaults to True so that INSERT ... RETURNING and DML persist.
    """
    should_commit = True if commit is None else commit
    with get_db_cursor(commit=should_commit) as cur:
        cur.execute(sql, params or ())
        if fetch == "all":
            rows = cur.fetchall()
            # Return list of standard Python dicts for clean handling across layers
            return [dict(row) for row in rows]
        elif fetch == "one":
            row = cur.fetchone()
            return dict(row) if row else None
        return cur.rowcount
