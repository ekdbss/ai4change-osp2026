import streamlit as st


st.set_page_config(
    page_title="학교 민원 AI 플랫폼",
    page_icon="",
    layout="wide",
)

st.title("학교 민원 AI 플랫폼")
st.caption("학부모 민원을 정제하고, 학교 담당자가 빠르게 처리할 수 있도록 돕는 민원 관리 서비스입니다.")

st.markdown(
    """
    이 서비스는 학부모가 작성한 민원을 AI가 중립적인 문장으로 정리하고,
    KoBERT 기반 분류 결과를 바탕으로 학교 담당자가 민원을 처리할 수 있도록 구성되어 있습니다.
    """
)

parent_col, admin_col = st.columns(2)

with parent_col:
    st.subheader("학부모")
    st.write("민원을 작성하고, 접수번호로 처리 현황을 확인합니다.")
    st.page_link("pages/1_submit_complaint.py", label="학부모 민원 접수로 이동")

with admin_col:
    st.subheader("관리자")
    st.write("접수된 민원을 확인하고 상태, 카테고리, 긴급도, 안내 코멘트를 관리합니다.")
    st.page_link("pages/2_admin_dashboard.py", label="관리자 민원 처리로 이동")

st.divider()

st.subheader("현재 MVP 기능")
st.write("- 학부모 민원 작성 및 AI 정제 미리보기")
st.write("- KoBERT 기반 민원 카테고리 추천")
st.write("- Gemini 기반 감정 정제 및 구조화")
st.write("- MySQL 민원 저장")
st.write("- 관리자 상태 변경, 카테고리 확정, 긴급도 설정, 학부모 안내 코멘트 저장")
st.write("- 접수일 기준 민원 통계 시각화")
