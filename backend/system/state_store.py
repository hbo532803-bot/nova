from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

from backend.database import get_db
from backend.db_init import initialize_all_tables
from backend.db_retry import run_db_write_with_retry

NovaState = Literal[
    "BOOTING",
    "IDLE",
    "SCANNING_MARKET",
    "PLANNING",
    "EXECUTING",
    "LEARNING",
    "HIBERNATING",
    "ERROR",
]


@dataclass(frozen=True)
class StateSnapshot:
    state: NovaState
    updated_at: str
    last_error: Optional[str] = None


class StateStore:
    """
    Persistent Nova state machine storage.
    State transitions are executed through the action spine (STATE_TRANSITION).
    """

    KEY = "nova_system_state"

    def ensure(self) -> None:
        initialize_all_tables(reset=False)

    def get(self) -> StateSnapshot:
        self.ensure()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT state, last_error, updated_at FROM nova_system_state WHERE id=1")
            row = cursor.fetchone()
            return StateSnapshot(
                state=row["state"],
                updated_at=str(row["updated_at"]),
                last_error=row["last_error"],
            )

    def set(self, new_state: NovaState, *, last_error: Optional[str] = None) -> StateSnapshot:
        self.ensure()
        now = datetime.utcnow()
        def _write(conn):
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE nova_system_state
                SET state = ?, last_error = ?, updated_at = ?
                WHERE id = 1
                """,
                (new_state, last_error, now),
            )
            conn.commit()
            return None

        run_db_write_with_retry("nova_system_state.update", _write)
        return self.get()

