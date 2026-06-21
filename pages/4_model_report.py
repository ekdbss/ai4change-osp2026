import json
from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(page_title="모델 평가", layout="wide")

st.title("KoBERT 모델 평가")
st.caption("직접 Fine-Tuning한 민원 분류 모델의 성능 지표를 확인합니다.")

metrics_path = Path("reports/metrics.json")
report_path = Path("reports/classification_report.txt")
matrix_path = Path("reports/confusion_matrix.png")

if not metrics_path.exists():
    st.warning("아직 모델 평가 결과가 없습니다.")
    st.markdown(
        """
        다음 순서로 평가 파일을 생성하세요.

        1. Gemini로 `data/raw/generated_complaints.csv` 생성
        2. 학습/검증/테스트 데이터 분리
        3. `python model/train_kobert.py` 실행
        4. `python model/evaluate.py` 실행
        """
    )
    st.stop()

metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

col1, col2, col3, col4 = st.columns(4)
col1.metric("Accuracy", f"{metrics.get('accuracy', 0):.4f}")
col2.metric("Precision", f"{metrics.get('precision', 0):.4f}")
col3.metric("Recall", f"{metrics.get('recall', 0):.4f}")
col4.metric("F1 Score", f"{metrics.get('f1', 0):.4f}")

if matrix_path.exists():
    st.subheader("Confusion Matrix")
    st.image(str(matrix_path))

if report_path.exists():
    st.subheader("Classification Report")
    st.code(report_path.read_text(encoding="utf-8"), language="text")

if "per_label" in metrics:
    st.subheader("라벨별 성능")
    st.dataframe(pd.DataFrame(metrics["per_label"]).T, use_container_width=True)

