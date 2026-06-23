from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from src.db.connection import get_connection


def get_columns(cursor, table_name: str) -> set[str]:
    cursor.execute(f"SHOW COLUMNS FROM {table_name}")
    return {row["Field"] for row in cursor.fetchall()}


def main() -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            complaint_columns = get_columns(cursor, "complaints")
            history_columns = get_columns(cursor, "complaint_status_history")
            statements = []

            if "ai_urgency" not in complaint_columns:
                statements.append(
                    "ALTER TABLE complaints "
                    "ADD COLUMN ai_urgency VARCHAR(20) NOT NULL DEFAULT '보통' AFTER ai_confidence"
                )
            if "final_urgency" not in complaint_columns:
                statements.append(
                    "ALTER TABLE complaints "
                    "ADD COLUMN final_urgency VARCHAR(20) NOT NULL DEFAULT '보통' AFTER ai_urgency"
                )
            if "urgency_confidence" not in complaint_columns:
                statements.append(
                    "ALTER TABLE complaints "
                    "ADD COLUMN urgency_confidence FLOAT NULL AFTER final_urgency"
                )
            if "prev_final_urgency" not in history_columns:
                statements.append(
                    "ALTER TABLE complaint_status_history "
                    "ADD COLUMN prev_final_urgency VARCHAR(20) AFTER new_final_category"
                )
            if "new_final_urgency" not in history_columns:
                statements.append(
                    "ALTER TABLE complaint_status_history "
                    "ADD COLUMN new_final_urgency VARCHAR(20) AFTER prev_final_urgency"
                )

            for statement in statements:
                cursor.execute(statement)

            try:
                cursor.execute("CREATE INDEX idx_complaints_final_urgency ON complaints(final_urgency)")
            except Exception:
                pass

        conn.commit()

    print(f"applied statements: {len(statements)}")


if __name__ == "__main__":
    main()
