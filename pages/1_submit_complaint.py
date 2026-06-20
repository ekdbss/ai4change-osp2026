import streamlit as st

from src.ai.gemini_service import GeminiService
from src.ai.kobert_predictor import KoBERTPredictor
from src.config import get_model_path
from src.db.connection import is_db_configured
from src.db.complaint_repository import create_complaint
from src.services.complaint_service import process_complaint
from src.services import session_store
from src.utils.validators import validate_complaint


st.set_page_config(page_title="민원 작성", layout="centered")


@st.cache_resource
def load_classifier() -> KoBERTPredictor:
    return KoBERTPredictor(get_model_path())


@st.cache_resource
def load_gemini() -> GeminiService:
    return GeminiService()


st.title("학부모 민원 작성")
st.caption("민원을 입력하면 KoBERT가 분류하고 Gemini가 정제 및 구조화를 수행합니다.")

with st.form("complaint_form"):
    title = st.text_input("민원 제목", placeholder="예: 담임 선생님 상담 요청")
    original_text = st.text_area(
        "민원 내용",
        placeholder="불편하신 사항을 사실 중심으로 작성해주세요.",
        height=180,
    )
    submitted = st.form_submit_button("AI 분석 후 접수", type="primary", use_container_width=True)

if submitted:
    errors = validate_complaint(title, original_text)
    if errors:
        for error in errors:
            st.warning(error)
    else:
        classifier = load_classifier()
        gemini_service = load_gemini()

        with st.spinner("민원을 분류하고 정제하는 중입니다..."):
            record = process_complaint(title, original_text, classifier, gemini_service)

        try:
            if is_db_configured():
                complaint_id = create_complaint(record)
                storage_message = f"MySQL에 저장되었습니다. 접수 번호: {complaint_id}"
            else:
                complaint_id = session_store.add_complaint(record)
                storage_message = f"데모 저장소에 저장되었습니다. 접수 번호: {complaint_id}"
        except Exception as exc:
            complaint_id = session_store.add_complaint(record)
            storage_message = f"DB 저장 실패로 데모 저장소에 임시 저장되었습니다. 사유: {exc}"

        st.success("민원이 접수되었습니다.")
        st.info(storage_message)

        if not record["kobert_model_available"]:
            st.warning("아직 Fine-Tuning된 KoBERT 모델이 없어 임시 키워드 분류기가 사용되었습니다.")
        if not record["gemini_model_available"]:
            st.warning("GEMINI_API_KEY가 없어 Gemini 대신 데모 정제 결과가 사용되었습니다.")

        col1, col2 = st.columns(2)
        col1.metric("KoBERT 분류", record["category"])
        col2.metric("신뢰도", f"{record['confidence']:.2f}")

        st.subheader("AI 정제본")
        st.success(record["refined_text"])

        st.subheader("구조화 결과")
        st.json(record["structured_json"], expanded=True)

