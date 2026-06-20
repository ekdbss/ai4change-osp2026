import pandas as pd
import streamlit as st

from src.ai.label_map import LABEL_TO_ID
from src.db.connection import is_db_configured
from src.db.complaint_repository import get_status_history as get_db_status_history
from src.db.complaint_repository import list_attachments as list_db_attachments
from src.db.complaint_repository import list_complaints as list_db_complaints
from src.db.complaint_repository import update_complaint_review as update_db_review
from src.services.auth_service import require_admin_login
from src.services import session_store

admin_user = require_admin_login()

CATEGORIES = list(LABEL_TO_ID.keys())
STATUSES = ["접수", "검토 중", "처리 완료", "보류"]
PRIORITIES = [1, 2, 3, 4, 5]


def priority_label(value: int) -> str:
    labels = {
        1: "1단계 - 긴급",
        2: "2단계 - 우선 검토",
        3: "3단계 - 일반",
        4: "4단계 - 낮음",
        5: "5단계 - 참고",
    }
    return labels.get(int(value), "3단계 - 일반")


def load_complaints() -> list[dict]:
    if is_db_configured():
        try:
            return list_db_complaints()
        except Exception as exc:
            st.warning(f"MySQL 조회에 실패해 데모 저장소를 표시합니다. 사유: {exc}")
    return session_store.list_complaints()


def load_attachments(complaint_id: int) -> list[dict]:
    if is_db_configured():
        try:
            return list_db_attachments(complaint_id, include_data=True)
        except Exception as exc:
            st.warning(f"첨부파일 조회에 실패했습니다. 사유: {exc}")
            return []
    return session_store.list_attachments(complaint_id)


def load_status_history(complaint_id: int) -> list[dict]:
    if is_db_configured():
        try:
            return get_db_status_history(complaint_id)
        except Exception as exc:
            st.warning(f"처리 이력 조회에 실패했습니다. 사유: {exc}")
            return []
    return session_store.get_status_history(complaint_id)


def save_review(
    complaint_id: int,
    status: str,
    final_category: str,
    priority_level: int,
    parent_visible_comment: str,
) -> None:
    memo = parent_visible_comment.strip()
    admin_id = admin_user.get("id")
    if is_db_configured():
        update_db_review(
            complaint_id=complaint_id,
            new_status=status,
            final_category=final_category,
            priority_level=priority_level,
            parent_visible_comment=parent_visible_comment,
            memo=memo,
            admin_id=admin_id,
        )
    else:
        session_store.update_complaint_review(
            complaint_id=complaint_id,
            new_status=status,
            final_category=final_category,
            priority_level=priority_level,
            parent_visible_comment=parent_visible_comment,
            memo=memo,
        )


def index_of(options: list, value, default: int = 0) -> int:
    try:
        return options.index(value)
    except ValueError:
        return default


st.title("관리자 민원 처리")
st.caption("AI가 정제한 민원을 확인하고, 담당자가 최종 카테고리와 처리 상태를 관리합니다.")

complaints = load_complaints()

if not complaints:
    st.info("아직 접수된 민원이 없습니다.")
    st.stop()

total = len(complaints)
received = sum(1 for item in complaints if item.get("status") == "접수")
in_progress = sum(1 for item in complaints if item.get("status") == "검토 중")
done = sum(1 for item in complaints if item.get("status") == "처리 완료")
urgent = sum(1 for item in complaints if int(item.get("priority_level") or 3) <= 1)

metric_cols = st.columns(5)
metric_cols[0].metric("전체 민원", total)
metric_cols[1].metric("신규 접수", received)
metric_cols[2].metric("검토 중", in_progress)
metric_cols[3].metric("처리 완료", done)
metric_cols[4].metric("긴급 민원", urgent)

st.divider()

filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([1, 1, 1, 1.4])
with filter_col1:
    status_filter = st.selectbox("상태", ["전체", *STATUSES])
with filter_col2:
    category_filter = st.selectbox("확정 카테고리", ["전체", *CATEGORIES])
with filter_col3:
    priority_filter = st.selectbox("긴급도", ["전체", *[priority_label(value) for value in PRIORITIES]])
with filter_col4:
    keyword = st.text_input("검색", placeholder="학생명, 학교, 제목, 정제본 검색")


def matches(item: dict) -> bool:
    final_category = item.get("final_category") or item.get("ai_category") or "기타"
    if status_filter != "전체" and item.get("status") != status_filter:
        return False
    if category_filter != "전체" and final_category != category_filter:
        return False
    if priority_filter != "전체":
        selected_priority = PRIORITIES[[priority_label(value) for value in PRIORITIES].index(priority_filter)]
        if int(item.get("priority_level") or 3) != selected_priority:
            return False
    if keyword:
        haystack = " ".join(
            [
                str(item.get("school_name", "")),
                str(item.get("student_name", "")),
                str(item.get("title", "")),
                str(item.get("refined_text", "")),
                str(item.get("original_text", "")),
            ]
        )
        if keyword.strip() not in haystack:
            return False
    return True


filtered = [item for item in complaints if matches(item)]

list_col, detail_col = st.columns([1.05, 1.35], gap="large")

with list_col:
    st.subheader("민원 목록")
    if not filtered:
        st.info("조건에 맞는 민원이 없습니다.")
        selected_id = None
    else:
        table_rows = [
            {
                "접수번호": item["id"],
                "접수일": str(item.get("created_at", ""))[:10],
                "학생": f"{item.get('student_class', '')} {item.get('student_name', '')}",
                "제목": item.get("title", ""),
                "AI 추천": item.get("ai_category", ""),
                "확정": item.get("final_category") or item.get("ai_category", ""),
                "긴급도": priority_label(int(item.get("priority_level") or 3)),
                "상태": item.get("status", ""),
            }
            for item in filtered
        ]
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

        selected_id = st.selectbox(
            "상세 확인할 민원",
            [item["id"] for item in filtered],
            format_func=lambda item_id: f"#{item_id} - {next(item['title'] for item in filtered if item['id'] == item_id)}",
        )

with detail_col:
    selected = next((item for item in complaints if item.get("id") == selected_id), None)
    if not selected:
        st.info("왼쪽에서 민원을 선택해주세요.")
    else:
        current_final_category = selected.get("final_category") or selected.get("ai_category") or "기타"
        current_priority = int(selected.get("priority_level") or 3)

        st.subheader(selected["title"])
        st.caption(
            f"접수번호 #{selected['id']} | "
            f"{selected.get('school_name', '')} | "
            f"{selected.get('student_grade', '')} {selected.get('student_class', '')} "
            f"{selected.get('student_number', '')}번 {selected.get('student_name', '')}"
        )

        info_cols = st.columns(3)
        info_cols[0].metric("AI 추천 카테고리", selected.get("ai_category", ""))
        info_cols[1].metric("확정 카테고리", current_final_category)
        info_cols[2].metric("긴급도", priority_label(current_priority))

        st.markdown("**AI 정제본**")
        st.success(selected.get("refined_text", ""))

        attachments = load_attachments(int(selected["id"]))
        if attachments:
            st.markdown("**첨부파일**")
            for attachment in attachments:
                file_name = attachment.get("file_name", "attachment")
                mime_type = attachment.get("mime_type") or ""
                file_data = attachment.get("file_data")
                if file_data and mime_type.startswith("image/"):
                    st.image(file_data, caption=file_name, use_container_width=True)
                elif file_data:
                    st.download_button(
                        label=f"{file_name} 다운로드",
                        data=file_data,
                        file_name=file_name,
                        mime=mime_type or "application/octet-stream",
                        key=f"download-{selected['id']}-{attachment.get('id', file_name)}",
                    )
                else:
                    st.write(f"- {file_name}")

        with st.expander("원문 보기"):
            st.write(selected.get("original_text", ""))

        st.divider()
        st.markdown("**처리 정보 수정**")

        edit_col1, edit_col2, edit_col3 = st.columns([1, 1, 1])
        with edit_col1:
            new_status = st.selectbox(
                "상태",
                STATUSES,
                index=index_of(STATUSES, selected.get("status", "접수")),
            )
        with edit_col2:
            new_category = st.selectbox(
                "관리자 확정 카테고리",
                CATEGORIES,
                index=index_of(CATEGORIES, current_final_category),
            )
        with edit_col3:
            new_priority = st.selectbox(
                "긴급도",
                PRIORITIES,
                index=index_of(PRIORITIES, current_priority, default=2),
                format_func=priority_label,
            )

        parent_comment = st.text_area(
            "학부모에게 표시할 안내 코멘트",
            value=selected.get("parent_visible_comment") or "",
            height=110,
            placeholder="예: 관련 내용을 확인 중이며, 담임교사 상담 후 추가 안내드리겠습니다.",
        )

        if st.button("처리 정보 저장", type="primary", use_container_width=True):
            try:
                save_review(
                    int(selected["id"]),
                    new_status,
                    new_category,
                    int(new_priority),
                    parent_comment,
                )
                st.success("처리 정보가 저장되었습니다.")
                st.rerun()
            except Exception as exc:
                st.error(f"저장에 실패했습니다. 사유: {exc}")

        history = load_status_history(int(selected["id"]))
        if history:
            st.divider()
            st.markdown("**처리 이력**")
            history_rows = [
                {
                    "변경일": str(item.get("changed_at", "")),
                    "상태": f"{item.get('prev_status') or '-'} -> {item.get('new_status') or '-'}",
                    "카테고리": f"{item.get('prev_final_category') or '-'} -> {item.get('new_final_category') or '-'}",
                    "긴급도": f"{item.get('prev_priority_level') or '-'} -> {item.get('new_priority_level') or '-'}",
                    "메모": item.get("memo") or "",
                }
                for item in history
            ]
            st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)
