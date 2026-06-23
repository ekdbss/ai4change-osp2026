import base64
import json

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.ai.gemini_service import GeminiService
from src.ai.kobert_predictor import KoBERTPredictor
from src.config import get_model_path
from src.db.connection import is_db_configured
from src.db.complaint_repository import create_complaint
from src.db.complaint_repository import list_complaints_for_parent as list_db_parent_complaints
from src.services.auth_service import require_parent_login
from src.services import session_store
from src.services.complaint_service import process_complaint
from src.utils.validators import validate_complaint, validate_student_info

parent_user = require_parent_login()

if "complaint_text_input" not in st.session_state:
    st.session_state["complaint_text_input"] = ""


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


def format_file_size(size: int | None) -> str:
    size = int(size or 0)
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    if size >= 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size} bytes"


def render_attachment_preview(item: dict, key_prefix: str) -> None:
    file_name = item.get("file_name", "attachment")
    mime_type = item.get("mime_type") or ""
    file_data = item.get("file_data")
    file_size = format_file_size(item.get("file_size"))

    st.caption(f"{file_name} · {file_size}")
    if not file_data:
        st.write("미리보기할 수 있는 파일 데이터가 없습니다.")
        return

    if mime_type.startswith("image/"):
        st.image(file_data, caption=file_name, use_container_width=True)
        return

    if mime_type == "application/pdf":
        encoded_pdf = base64.b64encode(file_data).decode("utf-8")
        st.markdown(
            f"""
            <iframe
                src="data:application/pdf;base64,{encoded_pdf}"
                width="100%"
                height="420"
                style="border:1px solid #e5e7eb;border-radius:6px;"
            ></iframe>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            "PDF 다운로드",
            data=file_data,
            file_name=file_name,
            mime=mime_type,
            key=f"{key_prefix}-{file_name}",
            use_container_width=True,
        )
        return

    st.download_button(
        "첨부파일 다운로드",
        data=file_data,
        file_name=file_name,
        mime=mime_type or "application/octet-stream",
        key=f"{key_prefix}-{file_name}",
        use_container_width=True,
    )


def render_tts_control(text: str, component_id: str, label: str = "내용 읽어주기") -> None:
    safe_text = json.dumps(str(text or ""), ensure_ascii=False)
    safe_component_id = component_id.replace("-", "_")
    components.html(
        f"""
        <div style="display:flex;gap:8px;align-items:center;margin:4px 0 12px 0;">
          <button
            id="{safe_component_id}_speak"
            style="border:1px solid #d1d5db;border-radius:6px;background:#ffffff;padding:7px 12px;cursor:pointer;font-size:14px;"
          >
            {label}
          </button>
          <button
            id="{safe_component_id}_stop"
            style="border:1px solid #d1d5db;border-radius:6px;background:#f9fafb;padding:7px 12px;cursor:pointer;font-size:14px;"
          >
            중지
          </button>
        </div>
        <script>
          const text_{safe_component_id} = {safe_text};
          const synth_{safe_component_id} = window.speechSynthesis;
          document.getElementById("{safe_component_id}_speak").onclick = () => {{
            if (!text_{safe_component_id}) return;
            synth_{safe_component_id}.cancel();
            const utterance = new SpeechSynthesisUtterance(text_{safe_component_id});
            utterance.lang = "ko-KR";
            utterance.rate = 0.95;
            synth_{safe_component_id}.speak(utterance);
          }};
          document.getElementById("{safe_component_id}_stop").onclick = () => {{
            synth_{safe_component_id}.cancel();
          }};
        </script>
        """,
        height=54,
    )


def render_browser_stt_pad(component_id: str) -> None:
    safe_component_id = component_id.replace("-", "_")
    components.html(
        f"""
        <div style="border:1px solid #e5e7eb;border-radius:8px;padding:12px;background:#ffffff;">
          <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px;">
            <button id="{safe_component_id}_start" style="border:1px solid #d1d5db;border-radius:6px;background:#ffffff;padding:7px 12px;cursor:pointer;font-size:14px;">받아쓰기 시작</button>
            <button id="{safe_component_id}_stop" style="border:1px solid #d1d5db;border-radius:6px;background:#f9fafb;padding:7px 12px;cursor:pointer;font-size:14px;">중지</button>
            <button id="{safe_component_id}_copy" style="border:1px solid #2563eb;border-radius:6px;background:#2563eb;color:#ffffff;padding:7px 12px;cursor:pointer;font-size:14px;">복사</button>
          </div>
          <textarea
            id="{safe_component_id}_text"
            placeholder="말한 내용이 여기에 표시됩니다."
            style="box-sizing:border-box;width:100%;min-height:96px;border:1px solid #d1d5db;border-radius:6px;padding:10px;font-size:14px;line-height:1.5;resize:vertical;"
          ></textarea>
          <div id="{safe_component_id}_status" style="margin-top:6px;color:#4b5563;font-size:13px;"></div>
        </div>
        <script>
          const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
          const statusEl = document.getElementById("{safe_component_id}_status");
          const textEl = document.getElementById("{safe_component_id}_text");
          let recognition = null;
          let finalText = "";
          let isListening = false;

          if (!SpeechRecognition) {{
            statusEl.textContent = "이 브라우저에서는 음성 인식을 지원하지 않습니다.";
            document.getElementById("{safe_component_id}_start").disabled = true;
          }} else {{
            recognition = new SpeechRecognition();
            recognition.lang = "ko-KR";
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.onstart = () => {{
              isListening = true;
              statusEl.textContent = "듣고 있습니다.";
            }};
            recognition.onerror = (event) => {{
              statusEl.textContent = "음성 인식이 중단되었습니다: " + event.error;
            }};
            recognition.onend = () => {{
              isListening = false;
              statusEl.textContent = "중지되었습니다.";
            }};
            recognition.onresult = (event) => {{
              let interimText = "";
              for (let i = event.resultIndex; i < event.results.length; i++) {{
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {{
                  finalText += transcript + " ";
                }} else {{
                  interimText += transcript;
                }}
              }}
              textEl.value = (finalText + interimText).trim();
            }};
          }}

          document.getElementById("{safe_component_id}_start").onclick = () => {{
            if (!recognition) return;
            if (isListening) return;
            try {{
              recognition.start();
            }} catch (error) {{
              statusEl.textContent = "음성 인식을 다시 시작할 수 없습니다.";
            }}
          }};
          document.getElementById("{safe_component_id}_stop").onclick = () => {{
            if (recognition) recognition.stop();
          }};
          document.getElementById("{safe_component_id}_copy").onclick = async () => {{
            const value = textEl.value.trim();
            if (!value) return;
            try {{
              await navigator.clipboard.writeText(value);
              statusEl.textContent = "복사되었습니다. 민원 내용 칸에 붙여넣어 주세요.";
            }} catch (error) {{
              textEl.focus();
              textEl.select();
              document.execCommand("copy");
              statusEl.textContent = "텍스트를 선택했습니다. 복사가 안 되면 직접 복사해 주세요.";
            }}
          }};
        </script>
        """,
        height=220,
    )


def save_pending_complaint() -> int:
    record = st.session_state["pending_complaint"]
    attachments = st.session_state.get("pending_attachments", [])

    if is_db_configured():
        return create_complaint(record, attachments)
    return session_store.add_complaint(record, attachments)


def load_parent_complaints() -> list[dict]:
    if is_db_configured():
        try:
            return list_db_parent_complaints(parent_user)
        except Exception as exc:
            st.warning(f"DB 조회에 실패해 데모 저장소를 확인합니다. 사유: {exc}")

    return [
        item
        for item in session_store.list_complaints()
        if item.get("school_name") == parent_user.get("school_name")
        and item.get("student_class") == parent_user.get("student_class")
        and item.get("student_name") == parent_user.get("student_name")
    ]


def status_badge(status: str) -> str:
    colors = {
        "접수": ("#0f766e", "#ccfbf1"),
        "검토 중": ("#1d4ed8", "#dbeafe"),
        "처리 완료": ("#166534", "#dcfce7"),
        "보류": ("#92400e", "#fef3c7"),
    }
    fg, bg = colors.get(status, ("#374151", "#f3f4f6"))
    return (
        f"<span style='display:inline-block;padding:0.25rem 0.65rem;"
        f"border-radius:999px;background:{bg};color:{fg};font-weight:700;'>{status}</span>"
    )


def status_cell_style(status: str) -> str:
    colors = {
        "접수": "background-color:#ccfbf1;color:#0f766e;font-weight:700;",
        "검토 중": "background-color:#dbeafe;color:#1d4ed8;font-weight:700;",
        "처리 완료": "background-color:#dcfce7;color:#166534;font-weight:700;",
        "보류": "background-color:#fef3c7;color:#92400e;font-weight:700;",
    }
    return colors.get(status, "")


st.title("학부모 민원 포털")
st.caption("민원 내용을 학교 담당자가 확인하기 쉬운 문장으로 정리한 뒤 접수합니다.")
st.info(f"{parent_user['parent_name']}님, 민원 접수와 처리 현황 조회를 이용할 수 있습니다.")

submit_tab, status_tab = st.tabs(["민원 접수", "내 민원 현황"])

with submit_tab:
    st.subheader("학생 정보")

    with st.expander("음성으로 민원 작성하기", expanded=False):
        st.caption("녹음 후 텍스트 변환을 누르면 민원 내용 칸에 반영됩니다.")
        audio_file = st.audio_input("민원 내용을 말로 녹음해 주세요.", key="complaint_audio_input")
        if st.button(
            "녹음 내용 텍스트로 변환",
            disabled=audio_file is None,
            use_container_width=True,
        ):
            gemini_service = load_gemini()
            if not gemini_service.model_available:
                st.warning("Gemini 연결값이 없어 녹음 파일을 텍스트로 변환할 수 없습니다.")
            else:
                with st.spinner("녹음 내용을 텍스트로 변환하고 있습니다."):
                    transcript, used_model = gemini_service.transcribe_audio(
                        audio_file.getvalue(),
                        getattr(audio_file, "type", None) or "audio/wav",
                    )

                if transcript and used_model:
                    current_text = st.session_state.get("complaint_text_input", "").strip()
                    if current_text:
                        st.session_state["complaint_text_input"] = f"{current_text}\n{transcript}".strip()
                    else:
                        st.session_state["complaint_text_input"] = transcript
                    st.success("녹음 내용을 민원 내용 칸에 넣었습니다.")
                    st.rerun()
                else:
                    st.warning("음성 변환에 실패했습니다. 잠시 후 다시 시도하거나 아래 받아쓰기를 이용해 주세요.")

        st.caption("브라우저 받아쓰기는 API 없이 동작합니다. 인식된 문장을 복사해 민원 내용 칸에 붙여넣을 수 있습니다.")
        render_browser_stt_pad("parent-complaint-stt")

    with st.form("parent_complaint_form"):
        info_col1, info_col2, info_col3 = st.columns([1.4, 0.8, 0.8])
        with info_col1:
            school_name = st.text_input("학교", value=parent_user.get("school_name", ""))
        with info_col2:
            student_grade = st.text_input("학년", value=parent_user.get("student_grade", ""))
        with info_col3:
            student_class = st.text_input("반", value=parent_user.get("student_class", ""))

        info_col4, info_col5 = st.columns([0.8, 1.2])
        with info_col4:
            student_number = st.text_input("출석번호", value=parent_user.get("student_number", ""))
        with info_col5:
            student_name = st.text_input("학생 이름", value=parent_user.get("student_name", ""))

        st.subheader("민원 내용")
        title = st.text_input("민원 제목", placeholder="예: 급식 알레르기 안내 확인 요청")
        original_text = st.text_area(
            "민원 내용",
            placeholder="상황, 요청 사항, 확인이 필요한 내용을 적어주세요.",
            height=180,
            key="complaint_text_input",
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
                "user_id": parent_user.get("id"),
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
            st.caption(f"AI 추천 긴급도: {pending.get('ai_urgency', '보통')}")

        with preview_col2:
            attachments = st.session_state.get("pending_attachments", [])
            st.markdown("**첨부파일**")
            if attachments:
                for index, item in enumerate(attachments, start=1):
                    with st.container(border=True):
                        render_attachment_preview(item, f"pending-attachment-{index}")
            else:
                st.write("첨부파일 없음")

        st.markdown("**정제된 민원 내용**")
        st.success(pending["refined_text"])
        render_tts_control(pending["refined_text"], "pending-refined-tts", "정제본 읽어주기")

        if pending["kobert_model_available"]:
            model_parts = []
            if pending.get("category_model_available"):
                model_parts.append("카테고리")
            if pending.get("urgency_model_available"):
                model_parts.append("긴급도")
            st.success(f"직접 Fine-Tuning한 KoBERT 모델이 {'/'.join(model_parts)} 판단에 사용되었습니다.")
        else:
            st.info("현재 Fine-Tuning된 KoBERT 모델이 없어 데모 분류/긴급도 판단기가 사용되었습니다.")
        for error in pending.get("load_errors", []):
            st.warning(error)
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
    st.subheader("내 민원 현황")
    st.write(
        f"{parent_user.get('school_name', '')} "
        f"{parent_user.get('student_grade', '')} {parent_user.get('student_class', '')} "
        f"{parent_user.get('student_number', '')}번 {parent_user.get('student_name', '')} 학생 기준으로 조회합니다."
    )

    parent_complaints = load_parent_complaints()
    if not parent_complaints:
        st.info("아직 조회되는 민원이 없습니다.")
    else:
        rows = [
            {
                "접수번호": item["id"],
                "접수일": str(item.get("created_at", ""))[:16],
                "제목": item.get("title", ""),
                "카테고리": item.get("final_category") or item.get("ai_category") or "",
                "상태": item.get("status", ""),
                "학교 안내 등록일": str(item.get("parent_comment_updated_at") or item.get("updated_at") or "")[:16],
            }
            for item in parent_complaints
        ]
        status_df = pd.DataFrame(rows)
        st.dataframe(
            status_df.style.map(status_cell_style, subset=["상태"]),
            use_container_width=True,
            hide_index=True,
        )

        selected_id = st.selectbox(
            "상세 보기할 민원",
            [item["id"] for item in parent_complaints],
            format_func=lambda item_id: f"#{item_id} - {next(item['title'] for item in parent_complaints if item['id'] == item_id)}",
        )
        result = next(item for item in parent_complaints if item["id"] == selected_id)

        st.divider()
        st.markdown(status_badge(result["status"]), unsafe_allow_html=True)
        st.subheader(result["title"])
        st.write(f"접수일: {result.get('created_at', '')}")
        st.write(f"담당 부서: {result.get('recommended_department') or '확인 중'}")

        st.markdown("**학교 안내 내용**")
        comment = result.get("parent_visible_comment")
        if comment:
            comment_time = result.get("parent_comment_updated_at") or result.get("updated_at")
            st.caption(f"등록일: {comment_time}")
            st.info(comment)
            render_tts_control(comment, f"comment-tts-{result['id']}", "학교 안내 읽어주기")
        else:
            st.write("아직 등록된 안내 내용이 없습니다.")

        st.markdown("**접수된 정제 민원**")
        st.write(result["refined_text"])
        render_tts_control(result["refined_text"], f"status-refined-tts-{result['id']}", "정제 민원 읽어주기")
