import pandas as pd
import streamlit as st

from src.db.connection import is_db_configured
from src.db.complaint_repository import list_complaints as list_db_complaints
from src.db.complaint_repository import update_status as update_db_status
from src.services import session_store


st.set_page_config(page_title="관리자 대시보드", layout="wide")

st.title("관리자 대시보드")
st.caption("접수된 민원을 조회하고 처리 상태를 변경합니다.")


def load_complaints() -> list[dict]:
    if is_db_configured():
        try:
            return list_db_complaints()
        except Exception as exc:
            st.warning(f"MySQL 조회 실패로 데모 저장소를 표시합니다. 사유: {exc}")
    return session_store.list_complaints()


def change_status(complaint_id: int, new_status: str) -> None:
    if is_db_configured():
        try:
            update_db_status(complaint_id, new_status)
            return
        except Exception as exc:
            st.warning(f"MySQL 상태 변경 실패로 데모 저장소만 변경합니다. 사유: {exc}")
    session_store.update_status(complaint_id, new_status)


complaints = load_complaints()

if not complaints:
    st.info("아직 접수된 민원이 없습니다.")
    st.stop()

total = len(complaints)
pending = sum(1 for item in complaints if item["status"] == "접수")
in_progress = sum(1 for item in complaints if item["status"] == "검토중")
done = sum(1 for item in complaints if item["status"] == "처리완료")

col1, col2, col3, col4 = st.columns(4)
col1.metric("전체 민원", total)
col2.metric("접수", pending)
col3.metric("검토중", in_progress)
col4.metric("처리완료", done)

st.divider()

filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 2])
with filter_col1:
    category_filter = st.selectbox(
        "카테고리",
        ["전체", "수업/학습 문제", "교사 태도/행동", "시설/환경", "급식", "생활지도/안전", "기타"],
    )
with filter_col2:
    status_filter = st.selectbox("상태", ["전체", "접수", "검토중", "처리완료", "보류"])
with filter_col3:
    keyword = st.text_input("검색", placeholder="제목, 원문, 정제본 검색")


def matches(item: dict) -> bool:
    if category_filter != "전체" and item["category"] != category_filter:
        return False
    if status_filter != "전체" and item["status"] != status_filter:
        return False
    if keyword:
        haystack = " ".join(
            [
                str(item.get("title", "")),
                str(item.get("original_text", "")),
                str(item.get("refined_text", "")),
            ]
        )
        if keyword not in haystack:
            return False
    return True


filtered = [item for item in complaints if matches(item)]

list_col, detail_col = st.columns([1, 1.5], gap="large")
selected_id = None

with list_col:
    st.subheader("민원 목록")
    if not filtered:
        st.info("조건에 맞는 민원이 없습니다.")
    else:
        table_rows = [
            {
                "id": item["id"],
                "제목": item["title"],
                "카테고리": item["category"],
                "상태": item["status"],
                "신뢰도": item["confidence"],
            }
            for item in filtered
        ]
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

        selected_id = st.selectbox(
            "상세 조회할 민원 ID",
            [item["id"] for item in filtered],
        )

with detail_col:
    selected = next((item for item in complaints if item["id"] == selected_id), None)
    if selected:
        st.subheader(selected["title"])
        st.caption(
            f"카테고리: {selected['category']} | 신뢰도: {selected['confidence']} | 상태: {selected['status']}"
        )

        st.markdown("**원문**")
        st.info(selected["original_text"])

        st.markdown("**개인정보 마스킹 원문**")
        st.info(selected.get("masked_text", selected["original_text"]))

        st.markdown("**AI 정제본**")
        st.success(selected["refined_text"])

        st.markdown("**구조화 결과**")
        st.json(selected["structured_json"], expanded=True)

        st.divider()
        new_status = st.selectbox(
            "상태 변경",
            ["접수", "검토중", "처리완료", "보류"],
            index=["접수", "검토중", "처리완료", "보류"].index(selected["status"])
            if selected["status"] in ["접수", "검토중", "처리완료", "보류"]
            else 0,
        )

        if st.button("상태 저장", type="primary", use_container_width=True):
            change_status(int(selected["id"]), new_status)
            st.success("상태가 변경되었습니다.")
            st.rerun()
    else:
        st.info("왼쪽에서 민원을 선택하면 상세 내용이 표시됩니다.")

