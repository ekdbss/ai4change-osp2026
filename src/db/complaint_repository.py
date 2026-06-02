from __future__ import annotations

import json
from typing import Any

from src.db.connection import get_connection


def create_complaint(record: dict[str, Any]) -> int:
    sql = """
        INSERT INTO complaints (
            title,
            original_text,
            masked_text,
            refined_text,
            structured_json,
            category,
            confidence,
            status,
            recommended_department
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        record["title"],
        record["original_text"],
        record["masked_text"],
        record["refined_text"],
        json.dumps(record["structured_json"], ensure_ascii=False),
        record["category"],
        record["confidence"],
        record.get("status", "접수"),
        record.get("recommended_department", ""),
    )

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            complaint_id = cursor.lastrowid
        conn.commit()
    return int(complaint_id)


def list_complaints() -> list[dict[str, Any]]:
    sql = """
        SELECT
            id,
            title,
            original_text,
            masked_text,
            refined_text,
            structured_json,
            category,
            confidence,
            status,
            recommended_department,
            created_at,
            updated_at
        FROM complaints
        ORDER BY created_at DESC
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

    for row in rows:
        raw_json = row.get("structured_json")
        if isinstance(raw_json, str):
            row["structured_json"] = json.loads(raw_json)
    return rows


def update_status(complaint_id: int, new_status: str, memo: str = "", admin_id: int | None = None) -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT status FROM complaints WHERE id = %s", (complaint_id,))
            row = cursor.fetchone()
            previous_status = row["status"] if row else None

            cursor.execute(
                "UPDATE complaints SET status = %s WHERE id = %s",
                (new_status, complaint_id),
            )
            cursor.execute(
                """
                INSERT INTO complaint_status_history (
                    complaint_id,
                    admin_id,
                    prev_status,
                    new_status,
                    memo
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (complaint_id, admin_id, previous_status, new_status, memo),
            )
        conn.commit()


def get_status_history(complaint_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, complaint_id, admin_id, prev_status, new_status, memo, changed_at
                FROM complaint_status_history
                WHERE complaint_id = %s
                ORDER BY changed_at DESC
                """,
                (complaint_id,),
            )
            return cursor.fetchall()

