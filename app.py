import streamlit as st


st.set_page_config(
    page_title="학교 민원 AI 플랫폼",
    page_icon="",
    layout="wide",
)

navigation = st.navigation(
    {
        "학부모": [
            st.Page(
                "pages/1_submit_complaint.py",
                title="민원 접수/현황",
            ),
        ],
        "관리자": [
            st.Page(
                "pages/2_admin_dashboard.py",
                title="민원 처리",
            ),
            st.Page(
                "pages/3_statistics.py",
                title="민원 통계",
            ),
            st.Page(
                "pages/4_model_report.py",
                title="AI 모델 리포트",
            ),
        ],
    }
)

navigation.run()
