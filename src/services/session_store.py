from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any

import streamlit as st


STORE_PATH = Path("data/processed/demo_complaints.json")


def _read_file_store() -> list[dict[str, Any]]:
    if not STORE_PATH.exists():
        return []
    return json.loads(STORE_PATH.read_text(encoding="utf-8"))


def _write_file_store(records: list[dict[str, Any]]) -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def ensure_store() -> None:
    if "demo_complaints" not in st.session_state:
        st.session_state.demo_complaints = _read_file_store()


def add_complaint(
    record: dict[str, Any],
    attachments: list[dict[str, Any]] | None = None,
) -> int:
    ensure_store()
    existing_ids = [int(item.get("id", 0)) for item in st.session_state.demo_complaints]
    complaint_id = max(existing_ids, default=0) + 1
    stored = {
        "id": complaint_id,
        **record,
        "attachments": [
            {
                "file_name": item.get("file_name", ""),
                "mime_type": item.get("mime_type", ""),
                "file_size": item.get("file_size", 0),
            }
            for item in attachments or []
        ],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    st.session_state.demo_complaints.insert(0, stored)
    _write_file_store(st.session_state.demo_complaints)
    return complaint_id


def list_complaints() -> list[dict[str, Any]]:
    ensure_store()
    if not st.session_state.demo_complaints:
        st.session_state.demo_complaints = _read_file_store()
    return st.session_state.demo_complaints


def update_status(complaint_id: int, new_status: str) -> None:
    update_complaint_review(complaint_id, new_status=new_status)


def update_complaint_review(
    complaint_id: int,
    new_status: str | None = None,
    final_category: str | None = None,
    final_urgency: str | None = None,
    priority_level: int | None = None,
    parent_visible_comment: str | None = None,
    memo: str = "",
) -> None:
    ensure_store()
    for complaint in st.session_state.demo_complaints:
        if complaint["id"] == complaint_id:
            previous_status = complaint.get("status", "접수")
            complaint["status"] = new_status or previous_status
            complaint["final_category"] = final_category or complaint.get("final_category")
            complaint["final_urgency"] = final_urgency or complaint.get("final_urgency", "보통")
            complaint["priority_level"] = int(priority_level or complaint.get("priority_level", 3))
            if parent_visible_comment is not None:
                complaint["parent_visible_comment"] = parent_visible_comment
            complaint.setdefault("status_history", []).insert(
                0,
                {
                    "prev_status": previous_status,
                    "new_status": complaint["status"],
                    "new_final_urgency": complaint["final_urgency"],
                    "memo": memo,
                    "changed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            )
            complaint["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            _write_file_store(st.session_state.demo_complaints)
            return


def get_complaint_for_parent(complaint_id: int, student_name: str) -> dict[str, Any] | None:
    ensure_store()
    for complaint in st.session_state.demo_complaints:
        if int(complaint.get("id", 0)) == complaint_id and complaint.get("student_name") == student_name:
            return complaint
    return None


def list_attachments(complaint_id: int) -> list[dict[str, Any]]:
    ensure_store()
    for complaint in st.session_state.demo_complaints:
        if int(complaint.get("id", 0)) == complaint_id:
            return complaint.get("attachments", [])
    return []


def get_status_history(complaint_id: int) -> list[dict[str, Any]]:
    ensure_store()
    for complaint in st.session_state.demo_complaints:
        if int(complaint.get("id", 0)) == complaint_id:
            return complaint.get("status_history", [])
    return []
