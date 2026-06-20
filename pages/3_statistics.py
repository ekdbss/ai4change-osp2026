import pandas as pd
import streamlit as st

from src.db.connection import is_db_configured
from src.db.complaint_repository import list_complaints as list_db_complaints
from src.services.auth_service import require_admin_login
from src.services import session_store


st.set_page_config(page_title="민원 통계", layout="wide")

require_admin_login()

st.title("민원 통계")
st.caption("접수일을 기준으로 카테고리별 민원 발생 흐름을 확인합니다.")


def load_complaints() -> list[dict]:
    if is_db_configured():
        try:
            return list_db_complaints()
        except Exception as exc:
            st.warning(f"MySQL 조회에 실패해 데모 저장소를 표시합니다. 사유: {exc}")
    return session_store.list_complaints()


complaints = load_complaints()
if not complaints:
    st.info("통계를 만들 민원이 없습니다.")
    st.stop()

rows = []
for item in complaints:
    created_at = item.get("created_at")
    rows.append(
        {
            "접수일": pd.to_datetime(created_at).date() if created_at else None,
            "카테고리": item.get("final_category") or item.get("ai_category") or item.get("category") or "기타",
            "상태": item.get("status", "접수"),
            "긴급도": int(item.get("priority_level") or 3),
            "학교": item.get("school_name", ""),
        }
    )

df = pd.DataFrame(rows).dropna(subset=["접수일"])

metric_cols = st.columns(4)
metric_cols[0].metric("전체 민원", len(df))
metric_cols[1].metric("긴급 민원", int((df["긴급도"] <= 1).sum()))
metric_cols[2].metric("처리 완료", int((df["상태"] == "처리 완료").sum()))
metric_cols[3].metric("카테고리 수", int(df["카테고리"].nunique()))

st.divider()

st.subheader("접수일 기준 카테고리별 추이")
daily = (
    df.groupby(["접수일", "카테고리"])
    .size()
    .reset_index(name="건수")
    .pivot(index="접수일", columns="카테고리", values="건수")
    .fillna(0)
    .sort_index()
)
st.line_chart(daily, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("카테고리별 누적 건수")
    category_counts = (
        df.groupby("카테고리")
        .size()
        .reset_index(name="건수")
        .sort_values("건수", ascending=False)
    )
    st.bar_chart(category_counts.set_index("카테고리"), use_container_width=True)

with col2:
    st.subheader("상태별 누적 건수")
    status_counts = (
        df.groupby("상태")
        .size()
        .reset_index(name="건수")
        .sort_values("건수", ascending=False)
    )
    st.bar_chart(status_counts.set_index("상태"), use_container_width=True)

st.subheader("통계 원자료")
st.dataframe(
    df.sort_values("접수일", ascending=False),
    use_container_width=True,
    hide_index=True,
)
