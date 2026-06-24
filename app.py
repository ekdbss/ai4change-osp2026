import streamlit as st


SERVICE_NAME = "학교민원 분류 AI"
SERVICE_TAGLINE = "카테고리·긴급도 자동 판단 및 민원 정제 서비스"
TEAM_CREDIT = "Made by SCC(숙크크) Team"

st.set_page_config(
    page_title=SERVICE_NAME,
    page_icon="",
    layout="wide",
)

st.sidebar.markdown(
    f"""
    <div style="padding:0.25rem 0 1rem 0;">
        <div style="
            color:#0f172a;
            font-size:1.12rem;
            font-weight:800;
            line-height:1.25;
            letter-spacing:0;">
            {SERVICE_NAME}
        </div>
        <div style="
            color:#475569;
            font-size:0.78rem;
            font-weight:600;
            margin-top:0.28rem;
            line-height:1.35;
            letter-spacing:0;">
            {SERVICE_TAGLINE}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
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
        ],
    }
)

st.sidebar.markdown(
    f"""
    <div style="
        margin-top:2rem;
        padding-top:0.85rem;
        border-top:1px solid #e2e8f0;
        color:#64748b;
        font-size:0.72rem;
        line-height:1.4;
        letter-spacing:0;">
        {TEAM_CREDIT}
    </div>
    """,
    unsafe_allow_html=True,
)

navigation.run()
