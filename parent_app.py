import streamlit as st
import anthropic
import json

# ── 페이지 설정 ──────────────────────────────────────────
st.set_page_config(page_title="민원 플랫폼 - 학부모", page_icon="📝", layout="centered")

st.title("📝 학부모 민원 접수")
st.caption("내용을 작성하면 AI가 사실 중심으로 정제해드립니다.")

# ── 세션 초기화 ──────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "refined" not in st.session_state:
    st.session_state.refined = None
if "structured" not in st.session_state:
    st.session_state.structured = None
if "step" not in st.session_state:
    st.session_state.step = "write"  # write | preview | done

# ── 탭 ───────────────────────────────────────────────────
tab_write, tab_history = st.tabs(["✏️ 민원 작성", "📋 내 민원 내역"])

# ════════════════════════════════════════════════════════
# 탭 1: 민원 작성
# ════════════════════════════════════════════════════════
with tab_write:

    # ── 완료 화면 ─────────────────────────────────────────
    if st.session_state.step == "done":
        st.success("✅ 민원이 성공적으로 접수되었습니다!")
        st.info("담당 선생님께 전달되었습니다. 처리 현황은 '내 민원 내역' 탭에서 확인하세요.")
        if st.button("새 민원 작성하기"):
            st.session_state.step = "write"
            st.session_state.refined = None
            st.session_state.structured = None
            st.rerun()

    # ── 작성 & 미리보기 화면 ─────────────────────────────
    else:
        title = st.text_input("민원 제목", placeholder="예) 담임 선생님 상담 요청")
        original = st.text_area(
            "민원 내용 (원문)",
            placeholder="불편하신 사항을 자유롭게 작성해 주세요.\nAI가 정중한 표현으로 다듬어드립니다.",
            height=150,
            disabled=(st.session_state.step == "preview"),
        )

        # ── 정제 버튼 ──────────────────────────────────────
        if st.session_state.step == "write":
            if st.button("✦ AI로 정제하기", type="primary", use_container_width=True):
                if not title.strip():
                    st.warning("제목을 입력해주세요.")
                elif not original.strip():
                    st.warning("민원 내용을 입력해주세요.")
                else:
                    with st.spinner("AI가 민원을 정제하고 있습니다..."):
                        try:
                            client = anthropic.Anthropic()
                            message = client.messages.create(
                                model="claude-sonnet-4-20250514",
                                max_tokens=1000,
                                messages=[
                                    {
                                        "role": "user",
                                        "content": f"""당신은 학교 민원을 정제하는 AI입니다.
아래 민원 원문으로 두 가지 작업을 수행하고 JSON으로만 응답하세요.
다른 설명 없이 JSON만 출력하세요.

1. refined: 감정적·과격한 표현을 사실 중심의 정중한 문장으로 변환
2. structured: 민원의 핵심 정보를 구조화
   - type: 민원 유형 (교사 태도 / 학교 시설 / 수업 문제 / 안전 / 기타)
   - urgency: 긴급도 (높음 / 보통 / 낮음)
   - summary: 핵심 요약 (1~2문장)
   - request: 요구사항

민원 원문:
"{original}"

응답 형식:
{{
  "refined": "정제된 민원 내용",
  "structured": {{
    "type": "민원 유형",
    "urgency": "긴급도",
    "summary": "핵심 요약",
    "request": "요구사항"
  }}
}}""",
                                    }
                                ],
                            )
                            raw = message.content[0].text
                            clean = raw.replace("```json", "").replace("```", "").strip()
                            result = json.loads(clean)
                            st.session_state.refined = result["refined"]
                            st.session_state.structured = result["structured"]
                            st.session_state.step = "preview"
                            st.session_state._title = title
                            st.session_state._original = original
                            st.rerun()
                        except Exception as e:
                            st.error(f"AI 정제 중 오류가 발생했습니다: {e}")

        # ── 미리보기 화면 ──────────────────────────────────
        if st.session_state.step == "preview" and st.session_state.refined:
            st.divider()
            st.subheader("📋 AI 정제 결과 미리보기")

            col_orig, col_ref = st.columns(2)
            with col_orig:
                st.markdown("**원문**")
                st.info(st.session_state._original)
            with col_ref:
                st.markdown("**AI 정제본**")
                st.success(st.session_state.refined)

            # 구조화 정보
            if st.session_state.structured:
                s = st.session_state.structured
                st.divider()
                st.subheader("🗂️ 자동 구조화 정보")

                urgency_color = {"높음": "🔴", "보통": "🟡", "낮음": "🔵"}.get(
                    s.get("urgency", ""), "⚪"
                )

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("민원 유형", s.get("type", "-"))
                with col2:
                    st.metric("긴급도", f"{urgency_color} {s.get('urgency', '-')}")

                st.markdown(f"**핵심 요약**  \n{s.get('summary', '-')}")
                st.markdown(f"**요구사항**  \n{s.get('request', '-')}")

            # 액션 버튼
            st.divider()
            col_back, col_submit = st.columns([1, 2])
            with col_back:
                if st.button("↩ 다시 작성", use_container_width=True):
                    st.session_state.step = "write"
                    st.session_state.refined = None
                    st.session_state.structured = None
                    st.rerun()
            with col_submit:
                if st.button("✅ 정제본으로 제출하기", type="primary", use_container_width=True):
                    # TODO: 백엔드 API 연동 (POST /complaints)
                    import datetime
                    new_complaint = {
                        "title": st.session_state._title,
                        "original": st.session_state._original,
                        "refined": st.session_state.refined,
                        "structured": st.session_state.structured,
                        "submitted_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "status": "접수됨",
                    }
                    st.session_state.history.append(new_complaint)
                    st.session_state.step = "done"
                    st.rerun()

# ════════════════════════════════════════════════════════
# 탭 2: 내 민원 내역
# ════════════════════════════════════════════════════════
with tab_history:
    st.subheader("내 민원 내역")

    if not st.session_state.history:
        st.info("아직 접수된 민원이 없습니다.")
    else:
        for i, c in enumerate(reversed(st.session_state.history)):
            status_icon = {"접수됨": "🔴", "처리중": "🟡", "완료": "🟢"}.get(c["status"], "⚪")
            with st.expander(f"{status_icon} {c['title']} — {c['submitted_at']}"):
                st.markdown(f"**상태:** {c['status']}")
                st.markdown(f"**핵심 요약:** {c['structured'].get('summary', '-') if c['structured'] else '-'}")
                st.markdown(f"**요구사항:** {c['structured'].get('request', '-') if c['structured'] else '-'}")
