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
            user_columns = get_columns(cursor, "users")
            admin_columns = get_columns(cursor, "admins")
            statements = []

            user_fields = [
                ("school_name", "VARCHAR(100)", "phone_masked"),
                ("student_grade", "VARCHAR(20)", "school_name"),
                ("student_class", "VARCHAR(50)", "student_grade"),
                ("student_number", "VARCHAR(20)", "student_class"),
                ("student_name", "VARCHAR(100)", "student_number"),
            ]
            for name, ddl, after in user_fields:
                if name not in user_columns:
                    statements.append(f"ALTER TABLE users ADD COLUMN {name} {ddl} AFTER {after}")

            admin_fields = [
                ("region_name", "VARCHAR(100)", "role"),
                ("school_name", "VARCHAR(100)", "region_name"),
            ]
            for name, ddl, after in admin_fields:
                if name not in admin_columns:
                    statements.append(f"ALTER TABLE admins ADD COLUMN {name} {ddl} AFTER {after}")

            for statement in statements:
                cursor.execute(statement)

            try:
                cursor.execute(
                    "CREATE INDEX idx_users_student "
                    "ON users(school_name, student_grade, student_class, student_number, student_name)"
                )
            except Exception:
                pass

        conn.commit()

    print(f"applied statements: {len(statements)}")


if __name__ == "__main__":
    main()
