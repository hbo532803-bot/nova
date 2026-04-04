import datetime

from backend.database import get_db
from backend.db_retry import run_db_write_with_retry


class CommandQueue:

    def ensure_table(self):
        return None

    # -----------------------------------
    # ADD COMMAND
    # -----------------------------------

    def add_command(self, command_text):
        def _write(conn):
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO nova_commands (command_text)
                VALUES (?)
                """,
                (command_text,),
            )
            conn.commit()
            return cursor.lastrowid

        return run_db_write_with_retry("nova_commands.insert", _write)

    # -----------------------------------
    # FETCH PENDING COMMANDS
    # -----------------------------------

    def fetch_pending(self):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            SELECT id, command_text, status
            FROM nova_commands
            WHERE status='PENDING'
            ORDER BY created_at ASC
            """)

            rows = cursor.fetchall()

        return rows

    # -----------------------------------
    # UPDATE STATUS
    # -----------------------------------

    def update_status(self, command_id, status, result=None):
        def _write(conn):
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE nova_commands
                SET status=?,
                    result=?,
                    updated_at=?
                WHERE id=?
                """,
                (
                    status,
                    result,
                    datetime.datetime.utcnow(),
                    command_id,
                ),
            )
            conn.commit()
            return None

        run_db_write_with_retry("nova_commands.update_status", _write)

    # -----------------------------------
    # FETCH HISTORY
    # -----------------------------------

    def fetch_recent(self, limit=20):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            SELECT id, command_text, status, result, created_at
            FROM nova_commands
            ORDER BY created_at DESC
            LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()

        return rows
