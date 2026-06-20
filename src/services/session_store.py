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


def add_complaint(record: dict[str, Any]) -> int:
    ensure_store()
    existing_ids = [int(item.get("id", 0)) for item in st.session_state.demo_complaints]
    complaint_id = max(existing_ids, default=0) + 1
    stored = {
        "id": complaint_id,
        **record,
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
    ensure_store()
    for complaint in st.session_state.demo_complaints:
        if complaint["id"] == complaint_id:
            complaint["status"] = new_status
            complaint["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            _write_file_store(st.session_state.demo_complaints)
            return
