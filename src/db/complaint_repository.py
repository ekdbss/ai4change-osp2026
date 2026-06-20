from __future__ import annotations

import json
from typing import Any

from src.db.connection import get_connection


def create_complaint(
    record: dict[str, Any],
    attachments: list[dict[str, Any]] | None = None,
) -> int:
    sql = """
        INSERT INTO complaints (
            user_id,
            school_name,
            student_grade,
            student_class,
            student_number,
            student_name,
            title,
            original_text,
            masked_text,
            refined_text,
            structured_json,
            ai_category,
            final_category,
            ai_confidence,
            priority_level,
            status,
            recommended_department,
            parent_visible_comment
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        record.get("user_id"),
        record.get("school_name", ""),
        record.get("student_grade", ""),
        record.get("student_class", ""),
        record.get("student_number", ""),
        record.get("student_name", ""),
        record["title"],
        record["original_text"],
        record.get("masked_text", ""),
        record["refined_text"],
        json.dumps(record.get("structured_json") or {}, ensure_ascii=False),
        record.get("ai_category") or record.get("category", "기타"),
        record.get("final_category") or record.get("ai_category") or record.get("category", "기타"),
        record.get("ai_confidence", record.get("confidence")),
        int(record.get("priority_level", 3)),
        record.get("status", "접수"),
        record.get("recommended_department", ""),
        record.get("parent_visible_comment", ""),
    )

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            complaint_id = int(cursor.lastrowid)
            _insert_attachments(cursor, complaint_id, attachments or [])
        conn.commit()
    return complaint_id


def list_complaints() -> list[dict[str, Any]]:
    sql = """
        SELECT
            id,
            user_id,
            school_name,
            student_grade,
            student_class,
            student_number,
            student_name,
            title,
            original_text,
            masked_text,
            refined_text,
            structured_json,
            ai_category,
            final_category,
            ai_confidence,
            priority_level,
            status,
            recommended_department,
            parent_visible_comment,
            created_at,
            updated_at
        FROM complaints
        ORDER BY priority_level ASC, created_at DESC
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

    return [_normalize_row(row) for row in rows]


def get_complaint_for_parent(complaint_id: int, student_name: str) -> dict[str, Any] | None:
    sql = """
        SELECT
            id,
            school_name,
            student_grade,
            student_class,
            student_number,
            student_name,
            title,
            refined_text,
            ai_category,
            final_category,
            priority_level,
            status,
            recommended_department,
            parent_visible_comment,
            created_at,
            updated_at
        FROM complaints
        WHERE id = %s AND student_name = %s
        LIMIT 1
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (complaint_id, student_name.strip()))
            row = cursor.fetchone()
    return _normalize_row(row) if row else None


def list_attachments(complaint_id: int, include_data: bool = False) -> list[dict[str, Any]]:
    file_data_field = ", file_data" if include_data else ""
    sql = f"""
        SELECT
            id,
            complaint_id,
            file_name,
            mime_type,
            file_size,
            uploaded_at
            {file_data_field}
        FROM complaint_attachments
        WHERE complaint_id = %s
        ORDER BY uploaded_at ASC
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (complaint_id,))
            return cursor.fetchall()


def update_complaint_review(
    complaint_id: int,
    new_status: str | None = None,
    final_category: str | None = None,
    priority_level: int | None = None,
    parent_visible_comment: str | None = None,
    memo: str = "",
    admin_id: int | None = None,
) -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT status, final_category, priority_level, parent_visible_comment
                FROM complaints
                WHERE id = %s
                """,
                (complaint_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"complaint_id={complaint_id} 민원을 찾을 수 없습니다.")

            next_status = new_status or row["status"]
            next_category = final_category or row["final_category"]
            next_priority = int(priority_level or row["priority_level"] or 3)
            next_parent_comment = (
                row.get("parent_visible_comment", "")
                if parent_visible_comment is None
                else parent_visible_comment
            )

            cursor.execute(
                """
                UPDATE complaints
                SET
                    status = %s,
                    final_category = %s,
                    priority_level = %s,
                    parent_visible_comment = %s
                WHERE id = %s
                """,
                (
                    next_status,
                    next_category,
                    next_priority,
                    next_parent_comment,
                    complaint_id,
                ),
            )
            cursor.execute(
                """
                INSERT INTO complaint_status_history (
                    complaint_id,
                    admin_id,
                    prev_status,
                    new_status,
                    prev_final_category,
                    new_final_category,
                    prev_priority_level,
                    new_priority_level,
                    memo,
                    is_parent_visible
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                """,
                (
                    complaint_id,
                    admin_id,
                    row["status"],
                    next_status,
                    row["final_category"],
                    next_category,
                    row["priority_level"],
                    next_priority,
                    memo,
                ),
            )
        conn.commit()


def update_status(
    complaint_id: int,
    new_status: str,
    memo: str = "",
    admin_id: int | None = None,
) -> None:
    update_complaint_review(
        complaint_id=complaint_id,
        new_status=new_status,
        memo=memo,
        admin_id=admin_id,
    )


def get_status_history(complaint_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    complaint_id,
                    admin_id,
                    prev_status,
                    new_status,
                    prev_final_category,
                    new_final_category,
                    prev_priority_level,
                    new_priority_level,
                    memo,
                    is_parent_visible,
                    changed_at
                FROM complaint_status_history
                WHERE complaint_id = %s
                ORDER BY changed_at DESC
                """,
                (complaint_id,),
            )
            return cursor.fetchall()


def list_category_priorities() -> list[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT category, priority_level, description, updated_at
                FROM category_priority_settings
                ORDER BY priority_level ASC, category ASC
                """
            )
            return cursor.fetchall()


def _insert_attachments(
    cursor: Any,
    complaint_id: int,
    attachments: list[dict[str, Any]],
) -> None:
    if not attachments:
        return

    sql = """
        INSERT INTO complaint_attachments (
            complaint_id,
            file_name,
            mime_type,
            file_size,
            file_path,
            file_data
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    for attachment in attachments:
        cursor.execute(
            sql,
            (
                complaint_id,
                attachment.get("file_name", ""),
                attachment.get("mime_type", ""),
                attachment.get("file_size", 0),
                attachment.get("file_path", ""),
                attachment.get("file_data"),
            ),
        )


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    raw_json = row.get("structured_json")
    if isinstance(raw_json, str):
        try:
            row["structured_json"] = json.loads(raw_json)
        except json.JSONDecodeError:
            row["structured_json"] = {}
    elif raw_json is None:
        row["structured_json"] = {}

    row["category"] = row.get("final_category") or row.get("ai_category") or "기타"
    row["confidence"] = row.get("ai_confidence")
    return row
