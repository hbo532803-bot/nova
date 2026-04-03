from __future__ import annotations

import logging
import random
import sqlite3
import time
from typing import Callable, TypeVar

from backend.database import get_db
from backend.system.observability import get_request_id

T = TypeVar("T")

_log = logging.getLogger("nova.db")


def _is_lock_error(exc: BaseException) -> bool:
    if not isinstance(exc, sqlite3.OperationalError):
        return False
    msg = str(exc).lower()
    return "database is locked" in msg or "database is busy" in msg or "locked" in msg


def run_db_write_with_retry(
    op: str,
    fn: Callable[[sqlite3.Connection], T],
    *,
    max_retries: int = 7,
    base_delay_s: float = 0.05,
    max_delay_s: float = 2.0,
) -> T:
    """
    Runs a write operation with exponential backoff on SQLite lock errors.

    - Opens a fresh connection per attempt (reduces poisoned-connection risk).
    - Logs structured warnings on retries.
    - Re-raises the final exception after max_retries is exceeded.
    """
    rid = get_request_id()

    attempt = 0
    while True:
        try:
            with get_db() as conn:
                return fn(conn)
        except Exception as e:
            if not _is_lock_error(e):
                raise

            if attempt >= int(max_retries):
                _log.error(
                    "sqlite_write_failed_lock",
                    extra={"op": op, "request_id": rid, "attempt": attempt, "max_retries": max_retries, "error": str(e)},
                )
                raise

            # exponential backoff with jitter
            delay = min(float(max_delay_s), float(base_delay_s) * (2**attempt))
            delay = delay * (0.5 + random.random())  # jitter in [0.5, 1.5)
            _log.warning(
                "sqlite_locked_retry",
                extra={"op": op, "request_id": rid, "attempt": attempt + 1, "sleep_s": round(delay, 4), "error": str(e)},
            )
            time.sleep(delay)
            attempt += 1

