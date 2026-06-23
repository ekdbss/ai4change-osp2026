import pandas as pd
import streamlit as st

from src.ai.label_map import LABEL_TO_ID
from src.ai.label_map import priority_for_urgency
from src.ai.model_artifacts import ensure_model_artifacts
from src.config import get_model_path
from src.db.connection import is_db_configured
from src.db.complaint_repository import get_status_history as get_db_status_history
from src.db.complaint_repository import list_attachments as list_db_attachments
from src.db.complaint_repository import list_complaints as list_db_complaints
from src.db.complaint_repository import update_complaint_review as update_db_review
from src.services.auth_service import require_admin_login
from src.services import session_store

admin_user = require_admin_login()

CATEGORIES = list(LABEL_TO_ID.keys())
URGENCIES = ["높음", "보통", "낮음"]
STATUSES = ["접수", "검토 중", "처리 완료", "보류"]
PRIORITIES = [1, 2, 3, 4, 5]
TRAINING_DATA_PATH = "data/raw/generated_complaints_final_1800.csv"


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
            return list_db_complaints(admin_user.get("school_name"))
        except Exception as exc:
            st.warning(f"MySQL 조회에 실패해 데모 저장소를 표시합니다. 사유: {exc}")
    return [
        item
        for item in session_store.list_complaints()
        if item.get("school_name") == admin_user.get("school_name")
    ]


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
    final_urgency: str,
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
            final_urgency=final_urgency,
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
            final_urgency=final_urgency,
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
st.caption(
    f"{admin_user.get('region_name', '')} / {admin_user.get('school_name', '')} "
    "민원만 표시됩니다."
)

artifact_status = ensure_model_artifacts(get_model_path())
with st.expander("KoBERT 학습 모델 상태", expanded=False):
    status_cols = st.columns(4)
    status_cols[0].metric("학습 데이터", "1,800건")
    status_cols[1].metric("카테고리 모델", "연결됨" if artifact_status["category_ready"] else "대기")
    status_cols[2].metric("긴급도 모델", "연결됨" if artifact_status["urgency_ready"] else "대기")
    status_cols[3].metric(
        "모델 크기",
        f"{artifact_status['category_size_mb'] + artifact_status['urgency_size_mb']:.1f} MB",
    )
    st.caption(f"데이터셋: {TRAINING_DATA_PATH}")
    if artifact_status["model_ready"]:
        st.success("접수 민원 처리 시 직접 Fine-Tuning한 KoBERT 모델이 우선 사용됩니다.")
    else:
        st.info("모델 zip을 설치하면 데모 판단기 대신 Fine-Tuning된 KoBERT 모델을 사용합니다.")
    if artifact_status.get("download_error"):
        st.warning(artifact_status["download_error"])

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
    urgency_filter = st.selectbox("확정 긴급도", ["전체", *URGENCIES])
with filter_col4:
    keyword = st.text_input("검색", placeholder="학생명, 학교, 제목, 정제본 검색")


def matches(item: dict) -> bool:
    final_category = item.get("final_category") or item.get("ai_category") or "기타"
    if status_filter != "전체" and item.get("status") != status_filter:
        return False
    if category_filter != "전체" and final_category != category_filter:
        return False
    final_urgency = item.get("final_urgency") or item.get("ai_urgency") or "보통"
    if urgency_filter != "전체" and final_urgency != urgency_filter:
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

st.subheader("민원 목록")
if not filtered:
    st.info("조건에 맞는 민원이 없습니다.")
    st.stop()

table_rows = [
    {
        "접수번호": item["id"],
        "접수 시간": str(item.get("created_at", ""))[:16],
        "학년": item.get("student_grade", ""),
        "반": item.get("student_class", ""),
        "출석번호": item.get("student_number", ""),
        "이름": item.get("student_name", ""),
        "제목": item.get("title", ""),
        "AI 카테고리": item.get("ai_category", ""),
        "확정 카테고리": item.get("final_category") or item.get("ai_category", ""),
        "AI 긴급도": item.get("ai_urgency", "보통"),
        "확정 긴급도": item.get("final_urgency") or item.get("ai_urgency", "보통"),
        "우선순위": priority_label(int(item.get("priority_level") or 3)),
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

selected = next((item for item in complaints if item.get("id") == selected_id), None)
if selected:
    st.divider()
    detail_left, detail_right = st.columns([1, 1], gap="large")
    with detail_left:
        current_final_category = selected.get("final_category") or selected.get("ai_category") or "기타"
        current_final_urgency = selected.get("final_urgency") or selected.get("ai_urgency") or "보통"
        current_priority = int(selected.get("priority_level") or 3)

        st.subheader(selected["title"])
        st.caption(
            f"접수번호 #{selected['id']} | "
            f"{selected.get('school_name', '')} | "
            f"{selected.get('student_grade', '')} {selected.get('student_class', '')} "
            f"{selected.get('student_number', '')}번 {selected.get('student_name', '')}"
        )

        info_cols = st.columns(4)
        info_cols[0].metric("AI 추천 카테고리", selected.get("ai_category", ""))
        info_cols[1].metric("AI 추천 긴급도", selected.get("ai_urgency", "보통"))
        info_cols[2].metric("확정 카테고리", current_final_category)
        info_cols[3].metric("확정 긴급도", current_final_urgency)

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

    with detail_right:
        st.divider()
        st.markdown("**처리 정보 수정**")

        edit_row1_col1, edit_row1_col2 = st.columns(2)
        with edit_row1_col1:
            new_status = st.selectbox(
                "상태",
                STATUSES,
                index=index_of(STATUSES, selected.get("status", "접수")),
            )
        with edit_row1_col2:
            new_category = st.selectbox(
                "확정 카테고리",
                CATEGORIES,
                index=index_of(CATEGORIES, current_final_category),
            )

        edit_row2_col1, edit_row2_col2 = st.columns(2)
        with edit_row2_col1:
            new_urgency = st.selectbox(
                "확정 긴급도",
                URGENCIES,
                index=index_of(URGENCIES, current_final_urgency, default=1),
            )
        with edit_row2_col2:
            suggested_priority = priority_for_urgency(new_urgency)
            new_priority = st.selectbox(
                "처리 우선순위",
                PRIORITIES,
                index=index_of(PRIORITIES, current_priority or suggested_priority, default=2),
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
                    new_urgency,
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
                    "긴급도": f"{item.get('prev_final_urgency') or '-'} -> {item.get('new_final_urgency') or '-'}",
                    "우선순위": f"{item.get('prev_priority_level') or '-'} -> {item.get('new_priority_level') or '-'}",
                    "메모": item.get("memo") or "",
                }
                for item in history
            ]
            st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)
