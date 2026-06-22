import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from src.db.connection import is_db_configured
from src.db.complaint_repository import list_complaints as list_db_complaints
from src.services.auth_service import require_admin_login
from src.services import session_store

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

admin_user = require_admin_login()

st.title("민원 통계")
st.caption(f"{admin_user.get('school_name', '')} 접수 민원을 기준으로 통계를 확인합니다.")


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


def horizontal_bar_chart(
    df: pd.DataFrame,
    label_column: str,
    value_column: str,
    colors: list[str],
):
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.barh(df[label_column], df[value_column], color=colors[: len(df)])
    ax.invert_yaxis()
    ax.set_xlabel("건수")
    ax.set_ylabel("")
    ax.tick_params(axis="y", labelrotation=0)
    for index, value in enumerate(df[value_column]):
        ax.text(value + 0.05, index, str(value), va="center")
    fig.tight_layout()
    return fig


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
            "긴급도": item.get("final_urgency") or item.get("ai_urgency") or "보통",
            "상태": item.get("status", "접수"),
            "우선순위": int(item.get("priority_level") or 3),
            "학교": item.get("school_name", ""),
        }
    )

df = pd.DataFrame(rows).dropna(subset=["접수일"])

metric_cols = st.columns(4)
metric_cols[0].metric("전체 민원", len(df))
metric_cols[1].metric("긴급 민원", int((df["긴급도"] == "높음").sum()))
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

st.subheader("접수일 기준 긴급도 추이")
daily_urgency = (
    df.groupby(["접수일", "긴급도"])
    .size()
    .reset_index(name="건수")
    .pivot(index="접수일", columns="긴급도", values="건수")
    .fillna(0)
    .sort_index()
)
st.line_chart(daily_urgency, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("카테고리별 누적 건수")
    category_counts = (
        df.groupby("카테고리")
        .size()
        .reset_index(name="건수")
        .sort_values("건수", ascending=False)
    )
    category_colors = ["#2563eb", "#16a34a", "#dc2626", "#f59e0b", "#7c3aed", "#0891b2"]
    st.pyplot(
        horizontal_bar_chart(category_counts, "카테고리", "건수", category_colors),
        use_container_width=True,
    )

with col2:
    st.subheader("상태별 누적 건수")
    status_counts = (
        df.groupby("상태")
        .size()
        .reset_index(name="건수")
        .sort_values("건수", ascending=False)
    )
    status_colors = ["#0f766e", "#1d4ed8", "#166534", "#92400e"]
    st.pyplot(
        horizontal_bar_chart(status_counts, "상태", "건수", status_colors),
        use_container_width=True,
    )

st.subheader("통계 원자료")
st.dataframe(
    df.sort_values("접수일", ascending=False),
    use_container_width=True,
    hide_index=True,
)
