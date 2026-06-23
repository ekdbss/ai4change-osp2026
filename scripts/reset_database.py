from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.db.connection import get_connection


TABLES = [
    "complaint_status_history",
    "complaint_attachments",
    "complaints",
    "statistics",
    "category_priority_settings",
    "admins",
    "users",
]


def main() -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            for table_name in TABLES:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                print(f"dropped {table_name}")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()

    print("database reset complete")


if __name__ == "__main__":
    main()
