import streamlit as st

from src.ai.gemini_service import GeminiService
from src.ai.kobert_predictor import KoBERTPredictor
from src.config import get_model_path
from src.db.connection import is_db_configured
from src.db.complaint_repository import create_complaint
from src.db.complaint_repository import get_complaint_for_parent as get_db_parent_complaint
from src.services.auth_service import require_parent_login
from src.services import session_store
from src.services.complaint_service import process_complaint
from src.utils.validators import validate_complaint, validate_student_info

parent_user = require_parent_login()


@st.cache_resource
def load_classifier() -> KoBERTPredictor:
    return KoBERTPredictor(get_model_path())


@st.cache_resource
def load_gemini() -> GeminiService:
    return GeminiService()


def to_attachment_records(uploaded_files: list) -> list[dict]:
    records = []
    for uploaded_file in uploaded_files:
        records.append(
            {
                "file_name": uploaded_file.name,
                "mime_type": uploaded_file.type,
                "file_size": uploaded_file.size,
                "file_data": uploaded_file.getvalue(),
            }
        )
    return records


def save_pending_complaint() -> int:
    record = st.session_state["pending_complaint"]
    attachments = st.session_state.get("pending_attachments", [])

    if is_db_configured():
        return create_complaint(record, attachments)
    return session_store.add_complaint(record, attachments)


def lookup_parent_complaint(complaint_id: int, student_name: str) -> dict | None:
    if is_db_configured():
        try:
            return get_db_parent_complaint(complaint_id, student_name)
        except Exception as exc:
            st.warning(f"DB 조회에 실패해 데모 저장소를 확인합니다. 사유: {exc}")
    return session_store.get_complaint_for_parent(complaint_id, student_name)


st.title("학부모 민원 포털")
st.caption("민원 내용을 학교 담당자가 확인하기 쉬운 문장으로 정리한 뒤 접수합니다.")
st.info(f"{parent_user['parent_name']}님, 민원 접수와 처리 현황 조회를 이용할 수 있습니다.")

submit_tab, status_tab = st.tabs(["민원 접수", "내 민원 현황"])

with submit_tab:
    st.subheader("학생 정보")

    with st.form("parent_complaint_form"):
        info_col1, info_col2, info_col3 = st.columns([1.4, 0.8, 0.8])
        with info_col1:
            school_name = st.text_input("학교", placeholder="예: 새봄초등학교")
        with info_col2:
            student_grade = st.text_input("학년", placeholder="예: 3학년")
        with info_col3:
            student_class = st.text_input("반", placeholder="예: 2반")

        info_col4, info_col5 = st.columns([0.8, 1.2])
        with info_col4:
            student_number = st.text_input("출석번호", placeholder="예: 15")
        with info_col5:
            student_name = st.text_input("학생 이름", placeholder="예: 김민준")

        st.subheader("민원 내용")
        title = st.text_input("민원 제목", placeholder="예: 급식 알레르기 안내 확인 요청")
        original_text = st.text_area(
            "민원 내용",
            placeholder="상황, 요청 사항, 확인이 필요한 내용을 적어주세요.",
            height=180,
        )
        uploaded_files = st.file_uploader(
            "첨부파일",
            type=["png", "jpg", "jpeg", "pdf"],
            accept_multiple_files=True,
            help="사진 또는 PDF 파일을 첨부할 수 있습니다.",
        )

        preview_submitted = st.form_submit_button(
            "AI 정제 미리보기",
            type="primary",
            use_container_width=True,
        )

    if preview_submitted:
        errors = []
        errors.extend(validate_student_info(school_name, student_class, student_name))
        errors.extend(validate_complaint(title, original_text))

        if errors:
            for error in errors:
                st.warning(error)
        else:
            classifier = load_classifier()
            gemini_service = load_gemini()
            complaint_meta = {
                "school_name": school_name.strip(),
                "student_grade": student_grade.strip(),
                "student_class": student_class.strip(),
                "student_number": student_number.strip(),
                "student_name": student_name.strip(),
            }

            with st.spinner("민원 내용을 정리하고 있습니다."):
                record = process_complaint(
                    title.strip(),
                    original_text.strip(),
                    classifier,
                    gemini_service,
                    complaint_meta=complaint_meta,
                )

            st.session_state["pending_complaint"] = record
            st.session_state["pending_attachments"] = to_attachment_records(uploaded_files or [])

    pending = st.session_state.get("pending_complaint")
    if pending:
        st.divider()
        st.subheader("AI 정제 미리보기")
        st.write("아래 내용으로 민원이 접수됩니다. 내용을 확인한 뒤 최종 접수해 주세요.")

        preview_col1, preview_col2 = st.columns([1, 1])
        with preview_col1:
            st.markdown("**접수 정보**")
            st.write(f"학교: {pending['school_name']}")
            st.write(
                "학생: "
                f"{pending.get('student_grade', '')} "
                f"{pending['student_class']} "
                f"{pending.get('student_number', '')}번 "
                f"{pending['student_name']}"
            )
            st.write(f"제목: {pending['title']}")
            st.caption(f"AI 추천 카테고리: {pending['ai_category']}")

        with preview_col2:
            attachments = st.session_state.get("pending_attachments", [])
            st.markdown("**첨부파일**")
            if attachments:
                for item in attachments:
                    st.write(f"- {item['file_name']} ({item['file_size']:,} bytes)")
            else:
                st.write("첨부파일 없음")

        st.markdown("**정제된 민원 내용**")
        st.success(pending["refined_text"])

        if not pending["kobert_model_available"]:
            st.info("현재 Fine-Tuning된 KoBERT 모델이 없어 데모 분류기가 사용되었습니다.")
        if not pending["gemini_model_available"]:
            st.info("Gemini 연결이 없어 데모 정제 결과가 사용되었습니다.")

        action_col1, action_col2 = st.columns([1, 1])
        with action_col1:
            if st.button("민원 접수하기", type="primary", use_container_width=True):
                try:
                    complaint_id = save_pending_complaint()
                    st.success(f"민원이 접수되었습니다. 접수번호는 {complaint_id}번입니다.")
                    st.session_state.pop("pending_complaint", None)
                    st.session_state.pop("pending_attachments", None)
                except Exception as exc:
                    st.error(f"민원 저장에 실패했습니다. DB 구조와 연결값을 확인해 주세요. 사유: {exc}")
        with action_col2:
            if st.button("다시 작성하기", use_container_width=True):
                st.session_state.pop("pending_complaint", None)
                st.session_state.pop("pending_attachments", None)
                st.rerun()

with status_tab:
    st.subheader("내 민원 현황 조회")
    st.write("접수번호와 학생 이름을 입력하면 처리 상태와 학교의 안내 내용을 확인할 수 있습니다.")

    lookup_col1, lookup_col2 = st.columns([0.8, 1.2])
    with lookup_col1:
        lookup_id = st.number_input("접수번호", min_value=1, step=1)
    with lookup_col2:
        lookup_student_name = st.text_input("학생 이름", placeholder="예: 김민준")

    if st.button("조회하기", type="primary"):
        if not lookup_student_name.strip():
            st.warning("학생 이름을 입력해주세요.")
        else:
            result = lookup_parent_complaint(int(lookup_id), lookup_student_name.strip())
            if not result:
                st.info("입력한 정보와 일치하는 민원이 없습니다.")
            else:
                st.success("민원 정보를 찾았습니다.")
                st.metric("현재 상태", result["status"])
                st.write(f"제목: {result['title']}")
                st.write(f"접수일: {result.get('created_at', '')}")
                st.write(f"담당 부서: {result.get('recommended_department') or '확인 중'}")

                st.markdown("**학교 안내 내용**")
                comment = result.get("parent_visible_comment")
                if comment:
                    st.info(comment)
                else:
                    st.write("아직 등록된 안내 내용이 없습니다.")

                st.markdown("**접수된 정제 민원**")
                st.write(result["refined_text"])
