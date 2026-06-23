from __future__ import annotations

import sys
from pathlib import Path

import pymysql


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.db.connection import get_connection

SCHEMA_PATH = ROOT_DIR / "sql" / "schema.sql"
SEED_ADMIN_PATH = ROOT_DIR / "sql" / "seed_admin.sql"


def load_statements(path: Path) -> list[str]:
    raw_sql = path.read_text(encoding="utf-8")
    statements = []
    for chunk in raw_sql.split(";"):
        statement = chunk.strip()
        if not statement:
            continue
        normalized = statement.upper()
        if normalized.startswith("CREATE DATABASE") or normalized.startswith("USE "):
            continue
        statements.append(statement)
    return statements


def execute_statement(cursor, statement: str) -> str:
    try:
        cursor.execute(statement)
        return "ok"
    except pymysql.err.MySQLError as exc:
        if exc.args and exc.args[0] in {1050, 1061}:
            return "skipped duplicate index"
        raise


def main() -> None:
    statements = load_statements(SCHEMA_PATH)
    if SEED_ADMIN_PATH.exists():
        statements.extend(load_statements(SEED_ADMIN_PATH))

    with get_connection() as conn:
        with conn.cursor() as cursor:
            for index, statement in enumerate(statements, start=1):
                result = execute_statement(cursor, statement)
                print(f"[{index:02d}/{len(statements):02d}] {result}")
        conn.commit()

    print("database initialization complete")


if __name__ == "__main__":
    main()
