import streamlit as st


st.set_page_config(
    page_title="학교 민원 AI 플랫폼",
    page_icon="",
    layout="wide",
)

st.title("AI 기반 학교 민원 감정 정제 및 자동 분류 플랫폼")
st.caption("KoBERT 직접 분류 모델과 Gemini 보조 정제를 결합한 민원 처리 MVP")

st.markdown(
    """
    이 MVP는 다음 흐름을 기준으로 구현되어 있습니다.

    1. 학부모가 민원 내용을 입력합니다.
    2. 직접 Fine-Tuning한 KoBERT 모델이 민원 카테고리를 분류합니다.
    3. Gemini가 감정 표현을 중립적으로 정제하고 행정 처리용 JSON으로 구조화합니다.
    4. MySQL에 원문, 정제본, 분류 결과, 처리 상태를 저장합니다.
    5. 관리자는 대시보드에서 민원을 조회하고 상태를 변경합니다.
    """
)

col1, col2, col3 = st.columns(3)
col1.metric("MVP 핵심 AI", "KoBERT 분류")
col2.metric("보조 AI", "Gemini 정제/구조화")
col3.metric("저장소", "MySQL")

st.info("왼쪽 사이드바에서 민원 작성, 관리자 대시보드, 통계, 모델 평가 화면으로 이동하세요.")

