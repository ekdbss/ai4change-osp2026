from __future__ import annotations

from html import escape
from math import ceil

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.ai.label_map import LABEL_TO_ID
from src.db.connection import is_db_configured
from src.db.complaint_repository import list_complaints as list_db_complaints
from src.services.auth_service import require_admin_login
from src.services import session_store

CATEGORIES = list(LABEL_TO_ID.keys())
URGENCIES = ["높음", "보통", "낮음"]
STATUSES = ["접수", "검토 중", "처리 완료", "보류"]
CATEGORY_COLORS = ["#ef4444", "#f97316", "#eab308", "#22c55e", "#06b6d4", "#8b5cf6"]
URGENCY_COLORS = {"높음": "#dc2626", "보통": "#facc15", "낮음": "#22c55e"}
STATUS_COLORS = ["#bfdbfe", "#60a5fa", "#2563eb", "#1e3a8a"]

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


def int_ticks(max_value: int, target_count: int = 5) -> list[int]:
    if max_value <= 0:
        return [0, 1]
    step = max(1, ceil(max_value / target_count))
    ticks = list(range(0, max_value + step, step))
    if ticks[-1] < max_value:
        ticks.append(max_value)
    return ticks


def complete_monthly_counts(df: pd.DataFrame, group_column: str, order: list[str]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["접수월", group_column, "건수"])

    month_df = df.copy()
    month_df["접수월"] = month_df["접수일"].dt.to_period("M").dt.to_timestamp()
    month_range = pd.date_range(month_df["접수월"].min(), month_df["접수월"].max(), freq="MS")
    base = pd.MultiIndex.from_product([month_range, order], names=["접수월", group_column]).to_frame(index=False)
    grouped = month_df.groupby(["접수월", group_column]).size().reset_index(name="건수")
    grouped["접수월"] = pd.to_datetime(grouped["접수월"])
    merged = base.merge(grouped, on=["접수월", group_column], how="left").fillna({"건수": 0})
    merged["건수"] = merged["건수"].astype(int)
    return merged


def ordered_counts(df: pd.DataFrame, group_column: str, order: list[str]) -> pd.DataFrame:
    counts = df.groupby(group_column).size().reindex(order, fill_value=0).reset_index(name="건수")
    counts["건수"] = counts["건수"].astype(int)
    return counts


def render_stacked_trend_chart(
    df: pd.DataFrame,
    group_column: str,
    order: list[str],
    colors: list[str],
    height: int = 370,
) -> None:
    width = 980
    margin = {"top": 34, "right": 168, "bottom": 60, "left": 54}
    plot_width = width - margin["left"] - margin["right"]
    plot_height = height - margin["top"] - margin["bottom"]

    months = sorted(pd.to_datetime(df["접수월"]).drop_duplicates().tolist())
    if not months:
        st.info("표시할 월별 데이터가 없습니다.")
        return

    pivot = (
        df.pivot_table(index="접수월", columns=group_column, values="건수", aggfunc="sum", fill_value=0)
        .reindex(months, fill_value=0)
        .reindex(columns=order, fill_value=0)
    )
    totals = pivot.sum(axis=1).astype(int)
    max_total = int(totals.max()) if len(totals) else 0
    y_ticks = int_ticks(max_total)
    y_max = max(y_ticks)
    slot_width = plot_width / max(len(months), 1)
    bar_width = min(96, slot_width * 0.58)

    def x_center(month_value) -> float:
        if len(months) == 1:
            return margin["left"] + plot_width / 2
        index = months.index(pd.to_datetime(month_value))
        return margin["left"] + slot_width * index + slot_width / 2

    def y_pos(value: int) -> float:
        if y_max == 0:
            return margin["top"] + plot_height
        return margin["top"] + plot_height - (plot_height * int(value) / y_max)

    grid_parts = []
    for tick in y_ticks:
        y = y_pos(tick)
        grid_parts.append(
            f'<line x1="{margin["left"]}" y1="{y:.1f}" x2="{margin["left"] + plot_width}" '
            f'y2="{y:.1f}" stroke="#e5e7eb" stroke-width="1" />'
        )
        grid_parts.append(
            f'<text x="{margin["left"] - 12}" y="{y + 4:.1f}" text-anchor="end" '
            f'font-size="12" fill="#475569">{tick}</text>'
        )

    x_labels = []
    for month_value in months:
        x = x_center(month_value)
        x_labels.append(
            f'<text x="{x:.1f}" y="{height - 25}" text-anchor="middle" '
            f'font-size="12" fill="#475569">{month_value.strftime("%Y-%m")}</text>'
        )

    bar_parts = []
    for month_value in months:
        center = x_center(month_value)
        x = center - bar_width / 2
        bottom_value = 0
        for label, color in zip(order, colors):
            value = int(pivot.loc[month_value, label])
            if value <= 0:
                continue
            top_value = bottom_value + value
            segment_y = y_pos(top_value)
            segment_height = y_pos(bottom_value) - segment_y
            bar_parts.append(
                f'<rect x="{x:.1f}" y="{segment_y:.1f}" width="{bar_width:.1f}" height="{segment_height:.1f}" '
                f'fill="{color}"><title>{month_value.strftime("%Y-%m")} / {escape(label)} / {value}건</title></rect>'
            )
            if segment_height >= 18:
                bar_parts.append(
                    f'<text x="{center:.1f}" y="{segment_y + segment_height / 2 + 4:.1f}" '
                    f'text-anchor="middle" font-size="12" font-weight="700" fill="#ffffff">{value}</text>'
                )
            bottom_value = top_value

        total = int(totals.loc[month_value])
        if total > 0:
            bar_parts.append(
                f'<text x="{center:.1f}" y="{max(y_pos(total) - 9, 16):.1f}" text-anchor="middle" '
                f'font-size="13" font-weight="700" fill="#111827">{total}건</text>'
            )

    legend_parts = []
    legend_x = margin["left"] + plot_width + 24
    for index, (label, color) in enumerate(zip(order, colors)):
        y = margin["top"] + index * 25
        legend_parts.append(f'<circle cx="{legend_x}" cy="{y}" r="5" fill="{color}" />')
        legend_parts.append(
            f'<text x="{legend_x + 12}" y="{y + 4}" font-size="13" fill="#334155">{escape(label)}</text>'
        )

    svg = f"""
    <div style="width:100%; overflow:hidden;">
      <svg viewBox="0 0 {width} {height}" width="100%" height="{height}" role="img">
        <rect width="{width}" height="{height}" fill="#ffffff" />
        <line x1="{margin["left"]}" y1="{margin["top"]}" x2="{margin["left"]}" y2="{margin["top"] + plot_height}" stroke="#cbd5e1" />
        <line x1="{margin["left"]}" y1="{margin["top"] + plot_height}" x2="{margin["left"] + plot_width}" y2="{margin["top"] + plot_height}" stroke="#cbd5e1" />
        {''.join(grid_parts)}
        {''.join(bar_parts)}
        {''.join(x_labels)}
        {''.join(legend_parts)}
      </svg>
    </div>
    """
    components.html(svg, height=height + 10, scrolling=False)


def render_bar_chart(df: pd.DataFrame, label_column: str, colors: list[str], height: int = 340) -> None:
    width = 720
    margin = {"top": 36, "right": 20, "bottom": 88, "left": 58}
    plot_width = width - margin["left"] - margin["right"]
    plot_height = height - margin["top"] - margin["bottom"]

    values = df["건수"].astype(int).tolist()
    labels = df[label_column].astype(str).tolist()
    max_count = max(values) if values else 0
    y_ticks = int_ticks(max_count)
    y_max = max(y_ticks)
    bar_slot = plot_width / max(len(labels), 1)
    bar_width = min(58, bar_slot * 0.58)

    def y_pos(value: int) -> float:
        if y_max == 0:
            return margin["top"] + plot_height
        return margin["top"] + plot_height - (plot_height * int(value) / y_max)

    grid_parts = []
    for tick in y_ticks:
        y = y_pos(tick)
        grid_parts.append(
            f'<line x1="{margin["left"]}" y1="{y:.1f}" x2="{margin["left"] + plot_width}" '
            f'y2="{y:.1f}" stroke="#e5e7eb" stroke-width="1" />'
        )
        grid_parts.append(
            f'<text x="{margin["left"] - 10}" y="{y + 4:.1f}" text-anchor="end" '
            f'font-size="14" fill="#475569">{tick}</text>'
        )

    bar_parts = []
    for index, (label, value) in enumerate(zip(labels, values)):
        center = margin["left"] + bar_slot * index + bar_slot / 2
        x = center - bar_width / 2
        y = y_pos(value)
        bar_height = margin["top"] + plot_height - y
        color = colors[index % len(colors)]
        bar_parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" '
            f'rx="5" fill="{color}"><title>{escape(label)} / {value}건</title></rect>'
        )
        bar_parts.append(
            f'<text x="{center:.1f}" y="{max(y - 10, 17):.1f}" text-anchor="middle" '
            f'font-size="16" font-weight="800" fill="#111827">{value}</text>'
        )
        bar_parts.append(
            f'<text x="{center:.1f}" y="{height - 42}" text-anchor="middle" '
            f'font-size="15" font-weight="700" fill="#334155">{escape(label)}</text>'
        )

    svg = f"""
    <div style="width:100%; overflow:hidden;">
      <svg viewBox="0 0 {width} {height}" width="100%" height="{height}" role="img">
        <rect width="{width}" height="{height}" fill="#ffffff" />
        <line x1="{margin["left"]}" y1="{margin["top"]}" x2="{margin["left"]}" y2="{margin["top"] + plot_height}" stroke="#cbd5e1" />
        <line x1="{margin["left"]}" y1="{margin["top"] + plot_height}" x2="{margin["left"] + plot_width}" y2="{margin["top"] + plot_height}" stroke="#cbd5e1" />
        {''.join(grid_parts)}
        {''.join(bar_parts)}
      </svg>
    </div>
    """
    components.html(svg, height=height + 10, scrolling=False)


complaints = load_complaints()
if not complaints:
    st.info("통계를 만들 민원이 없습니다.")
    st.stop()

rows = []
for item in complaints:
    created_at = item.get("created_at")
    rows.append(
        {
            "접수일": pd.to_datetime(created_at).normalize() if created_at else None,
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

st.subheader("접수월 기준 카테고리별 분포 추이")
monthly_category = complete_monthly_counts(df, "카테고리", CATEGORIES)
render_stacked_trend_chart(monthly_category, "카테고리", CATEGORIES, CATEGORY_COLORS)

st.subheader("접수월 기준 긴급도 분포 추이")
monthly_urgency = complete_monthly_counts(df, "긴급도", URGENCIES)
render_stacked_trend_chart(monthly_urgency, "긴급도", URGENCIES, [URGENCY_COLORS[item] for item in URGENCIES])

col1, col2 = st.columns(2)

with col1:
    st.subheader("카테고리별 누적 건수")
    category_counts = ordered_counts(df, "카테고리", CATEGORIES)
    render_bar_chart(category_counts, "카테고리", CATEGORY_COLORS)

with col2:
    st.subheader("상태별 누적 건수")
    status_counts = ordered_counts(df, "상태", STATUSES)
    render_bar_chart(status_counts, "상태", STATUS_COLORS)

st.subheader("통계 원자료")
raw_df = df.copy()
raw_df["접수일"] = raw_df["접수일"].dt.strftime("%Y-%m-%d")
st.dataframe(
    raw_df.sort_values("접수일", ascending=False),
    use_container_width=True,
    hide_index=True,
)
