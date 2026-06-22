from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.ai.label_map import LABEL_TO_ID, normalize_category
from src.config import get_model_path
from src.services.auth_service import require_admin_login


admin_user = require_admin_login()

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT_DIR / "data/raw/generated_complaints.csv"
PROCESSED_DIR = ROOT_DIR / "data/processed"
REPORT_DIR = ROOT_DIR / "reports"
MODEL_DIR = Path(get_model_path())


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def render_metric_block(title: str, metrics: dict) -> None:
    st.markdown(f"**{title}**")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Accuracy", f"{metrics.get('accuracy', 0):.3f}")
    col2.metric("Precision", f"{metrics.get('precision', 0):.3f}")
    col3.metric("Recall", f"{metrics.get('recall', 0):.3f}")
    col4.metric("F1", f"{metrics.get('f1', 0):.3f}")


def model_exists(task_name: str) -> bool:
    return (MODEL_DIR / task_name / "config.json").exists()


st.title("AI 모델 리포트")
st.caption(f"{admin_user.get('school_name', '')} 관리자 검증용 화면입니다.")

model_col1, model_col2, model_col3 = st.columns(3)
model_col1.metric("카테고리 모델", "연결됨" if model_exists("category") else "없음")
model_col2.metric("긴급도 모델", "연결됨" if model_exists("urgency") else "없음")
model_col3.metric("모델 경로", str(MODEL_DIR.name))

if DATA_PATH.exists():
    dataset = pd.read_csv(DATA_PATH)
    category_column = "category" if "category" in dataset.columns else "label"
    dataset["category"] = dataset[category_column].map(normalize_category)

    st.subheader("학습 데이터셋")
    data_col1, data_col2 = st.columns([1, 2])
    data_col1.metric("전체 문장 수", f"{len(dataset):,}")
    data_col1.metric("카테고리 수", f"{dataset['category'].nunique():,}")
    counts = (
        dataset["category"]
        .value_counts()
        .reindex(LABEL_TO_ID.keys(), fill_value=0)
        .reset_index()
    )
    counts.columns = ["카테고리", "건수"]
    data_col2.dataframe(counts, use_container_width=True, hide_index=True)
else:
    st.warning("학습 데이터셋 파일을 찾을 수 없습니다.")

if PROCESSED_DIR.exists():
    split_rows = []
    for split_name in ["train", "valid", "test"]:
        split_path = PROCESSED_DIR / f"{split_name}.csv"
        if split_path.exists():
            split_rows.append({"데이터": split_name, "건수": len(pd.read_csv(split_path))})
    if split_rows:
        st.dataframe(pd.DataFrame(split_rows), use_container_width=True, hide_index=True)

metrics = load_json(REPORT_DIR / "multitask_metrics.json")
if not metrics:
    st.info("아직 평가 결과가 없습니다. `python model/evaluate.py` 실행 후 확인할 수 있습니다.")
    st.stop()

st.subheader("성능 지표")
render_metric_block("카테고리 분류 모델", metrics.get("category", {}))
render_metric_block("긴급도 판단 모델", metrics.get("urgency", {}))

st.subheader("혼동행렬")
matrix_col1, matrix_col2 = st.columns(2)
with matrix_col1:
    category_matrix = REPORT_DIR / "category_confusion_matrix.png"
    if category_matrix.exists():
        st.image(str(category_matrix), caption="카테고리 분류 혼동행렬", use_container_width=True)
with matrix_col2:
    urgency_matrix = REPORT_DIR / "urgency_confusion_matrix.png"
    if urgency_matrix.exists():
        st.image(str(urgency_matrix), caption="긴급도 판단 혼동행렬", use_container_width=True)

st.subheader("상세 리포트")
with st.expander("카테고리 분류 Classification Report"):
    st.code(load_text(REPORT_DIR / "category_classification_report.txt") or "리포트 없음")
with st.expander("긴급도 판단 Classification Report"):
    st.code(load_text(REPORT_DIR / "urgency_classification_report.txt") or "리포트 없음")
