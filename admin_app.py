import streamlit as st

# ── 페이지 설정 ──────────────────────────────────────────
st.set_page_config(page_title="민원 플랫폼 - 관리자", page_icon="🏫", layout="wide")

st.title("🏫 민원 관리 대시보드")
st.caption("선생님 / 행정 담당자용 화면입니다.")

# ── 더미 데이터 (백엔드 연동 전) ─────────────────────────
if "complaints" not in st.session_state:
    st.session_state.complaints = [
        {
            "id": 1,
            "title": "담임 선생님 태도 문제",
            "original": "그 선생님 진짜 너무하는 거 아닌가요? 우리 아이한테 왜 그렇게 함!!!",
            "refined": "담임 선생님의 지도 방식이 자녀에게 부정적인 영향을 미치고 있어 개선을 요청드립니다.",
            "structured": {
                "type": "교사 태도",
                "urgency": "높음",
                "summary": "담임 교사의 언행으로 인해 학생이 심리적 불편함을 느끼고 있음.",
                "request": "담임 교사와의 면담 및 재발 방지 대책 마련 요청",
            },
            "submitted_at": "2026-05-23 09:12",
            "status": "접수됨",
        },
        {
            "id": 2,
            "title": "급식 위생 문제",
            "original": "급식에 벌레가 나왔어요. 어떻게 이럴 수가 있죠?",
            "refined": "오늘 자녀의 급식에서 이물질이 발견되었습니다. 위생 점검을 요청드립니다.",
            "structured": {
                "type": "학교 시설",
                "urgency": "높음",
                "summary": "급식 이물질 발견으로 위생 관리 점검 필요.",
                "request": "급식 위생 점검 및 재발 방지 조치 요청",
            },
            "submitted_at": "2026-05-23 11:30",
            "status": "처리중",
        },
        {
            "id": 3,
            "title": "수학 수업 진도 관련",
            "original": "진도가 너무 빠른 것 같아요. 아이가 따라가기 힘들어해요.",
            "refined": "수학 과목의 수업 진도에 대해 검토를 요청드립니다.",
            "structured": {
                "type": "수업 문제",
                "urgency": "보통",
                "summary": "수업 진도가 학생 수준에 비해 빠르게 진행되고 있어 보충 지도 요청.",
                "request": "수업 속도 조정 또는 보충 학습 자료 제공 요청",
            },
            "submitted_at": "2026-05-22 16:00",
            "status": "완료",
        },
    ]

complaints = st.session_state.complaints

# ── 통계 카드 ─────────────────────────────────────────────
total     = len(complaints)
pending   = sum(1 for c in complaints if c["status"] == "접수됨")
inprog    = sum(1 for c in complaints if c["status"] == "처리중")
done      = sum(1 for c in complaints if c["status"] == "완료")

col1, col2, col3, col4 = st.columns(4)
col1.metric("📋 전체 민원", total)
col2.metric("🔴 미처리 (접수됨)", pending)
col3.metric("🟡 처리중", inprog)
col4.metric("🟢 완료", done)

st.divider()

# ── 필터 ─────────────────────────────────────────────────
filter_status = st.radio(
    "상태 필터",
    ["전체", "접수됨", "처리중", "완료"],
    horizontal=True,
)

filtered = complaints if filter_status == "전체" else [
    c for c in complaints if c["status"] == filter_status
]

st.divider()

# ── 목록 + 상세 레이아웃 ──────────────────────────────────
list_col, detail_col = st.columns([1, 1.4], gap="large")

# 선택된 민원 ID 세션 관리
if "selected_id" not in st.session_state:
    st.session_state.selected_id = None

# ── 왼쪽: 민원 목록 ───────────────────────────────────────
with list_col:
    st.subheader("민원 목록")

    if not filtered:
        st.info("해당 상태의 민원이 없습니다.")

    for c in filtered:
        urgency_icon = {"높음": "🔴", "보통": "🟡", "낮음": "🔵"}.get(
            c["structured"]["urgency"], "⚪"
        )
        status_icon = {"접수됨": "🔴", "처리중": "🟡", "완료": "🟢"}.get(c["status"], "⚪")

        is_selected = st.session_state.selected_id == c["id"]
        btn_label = f"{'▶ ' if is_selected else ''}{c['title']}"

        if st.button(
            f"{status_icon} {btn_label}\n{urgency_icon} 긴급도: {c['structured']['urgency']}  |  {c['submitted_at']}",
            key=f"btn_{c['id']}",
            use_container_width=True,
            type="primary" if is_selected else "secondary",
        ):
            st.session_state.selected_id = c["id"]
            st.rerun()

# ── 오른쪽: 상세 패널 ─────────────────────────────────────
with detail_col:
    selected = next(
        (c for c in complaints if c["id"] == st.session_state.selected_id), None
    )

    if selected is None:
        st.info("👈 왼쪽에서 민원을 선택하면 상세 내용이 표시됩니다.")
    else:
        status_icon = {"접수됨": "🔴", "처리중": "🟡", "완료": "🟢"}.get(
            selected["status"], "⚪"
        )
        st.subheader(f"{selected['title']}")
        st.caption(f"접수일시: {selected['submitted_at']}  |  상태: {status_icon} {selected['status']}")

        # 원문 / 정제본
        st.markdown("**원문**")
        st.info(selected["original"])

        st.markdown("**AI 정제본**")
        st.success(selected["refined"])

        # 구조화 정보
        st.divider()
        st.markdown("**🗂️ 구조화 정보**")
        s = selected["structured"]
        urgency_icon = {"높음": "🔴", "보통": "🟡", "낮음": "🔵"}.get(s["urgency"], "⚪")

        c1, c2 = st.columns(2)
        c1.metric("민원 유형", s["type"])
        c2.metric("긴급도", f"{urgency_icon} {s['urgency']}")
        st.markdown(f"**핵심 요약:** {s['summary']}")
        st.markdown(f"**요구사항:** {s['request']}")

        # 상태 변경 버튼
        st.divider()
        status_cycle = {"접수됨": "처리중", "처리중": "완료"}

        if selected["status"] in status_cycle:
            next_status = status_cycle[selected["status"]]
            if st.button(
                f"→ '{next_status}'으로 변경",
                type="primary",
                use_container_width=True,
                key=f"change_{selected['id']}",
            ):
                # TODO: 백엔드 API 연동 (PATCH /complaints/{id})
                for c in st.session_state.complaints:
                    if c["id"] == selected["id"]:
                        c["status"] = next_status
                        break
                st.rerun()
        else:
            st.success("✅ 처리가 완료된 민원입니다.")
