from collections import Counter

import pandas as pd
import streamlit as st

from src.db.connection import is_db_configured
from src.db.complaint_repository import list_complaints as list_db_complaints
from src.services import session_store


st.set_page_config(page_title="통계", layout="wide")

st.title("민원 통계")
st.caption("카테고리별, 상태별 민원 분포를 확인합니다.")


def load_complaints() -> list[dict]:
    if is_db_configured():
        try:
            return list_db_complaints()
        except Exception as exc:
            st.warning(f"MySQL 조회 실패로 데모 저장소를 표시합니다. 사유: {exc}")
    return session_store.list_complaints()


complaints = load_complaints()
if not complaints:
    st.info("통계를 만들 민원이 없습니다.")
    st.stop()

category_counts = Counter(item["category"] for item in complaints)
status_counts = Counter(item["status"] for item in complaints)

col1, col2 = st.columns(2)

with col1:
    st.subheader("카테고리별 민원 수")
    category_df = pd.DataFrame(
        [{"카테고리": key, "건수": value} for key, value in category_counts.items()]
    )
    st.bar_chart(category_df.set_index("카테고리"))

with col2:
    st.subheader("상태별 민원 수")
    status_df = pd.DataFrame(
        [{"상태": key, "건수": value} for key, value in status_counts.items()]
    )
    st.bar_chart(status_df.set_index("상태"))

st.subheader("원자료")
st.dataframe(
    pd.DataFrame(
        [
            {
                "id": item["id"],
                "제목": item["title"],
                "카테고리": item["category"],
                "신뢰도": item["confidence"],
                "상태": item["status"],
                "추천 부서": item.get("recommended_department", ""),
                "접수일": item.get("created_at", ""),
            }
            for item in complaints
        ]
    ),
    use_container_width=True,
    hide_index=True,
)

