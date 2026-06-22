from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import torch
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from transformers import AutoModelForSequenceClassification, AutoTokenizer

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from src.ai.label_map import LABEL_TO_ID, URGENCY_TO_ID, normalize_category

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

MODEL_DIR = ROOT_DIR / "model/saved_model"
TEST_PATH = ROOT_DIR / "data/processed/test.csv"
REPORT_DIR = ROOT_DIR / "reports"


def evaluate_task(
    task_name: str,
    label_column: str,
    label_map: dict[str, int],
    df: pd.DataFrame,
) -> dict:
    task_model_dir = MODEL_DIR / task_name
    if not task_model_dir.exists():
        raise FileNotFoundError(f"저장된 {task_name} 모델이 없습니다: {task_model_dir}")

    id_to_label = {value: key for key, value in label_map.items()}
    tokenizer = AutoTokenizer.from_pretrained(str(task_model_dir))
    model = AutoModelForSequenceClassification.from_pretrained(str(task_model_dir))
    model.eval()

    true_ids = [label_map[label] for label in df[label_column]]
    predictions = []

    for text in df["text"]:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
        with torch.no_grad():
            outputs = model(**inputs)
            predictions.append(int(torch.argmax(outputs.logits, dim=1).item()))

    accuracy = accuracy_score(true_ids, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        true_ids,
        predictions,
        average="weighted",
        zero_division=0,
    )

    target_names = [id_to_label[index] for index in range(len(id_to_label))]
    report = classification_report(
        true_ids,
        predictions,
        target_names=target_names,
        zero_division=0,
    )
    matrix = confusion_matrix(true_ids, predictions)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / f"{task_name}_classification_report.txt").write_text(report, encoding="utf-8")
    metrics = {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }
    (REPORT_DIR / f"{task_name}_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    display = ConfusionMatrixDisplay(confusion_matrix=matrix, display_labels=target_names)
    display.plot(cmap="Blues", xticks_rotation=45)
    plt.tight_layout()
    plt.savefig(REPORT_DIR / f"{task_name}_confusion_matrix.png", dpi=160)
    plt.close()
    return metrics


def main() -> None:
    if not TEST_PATH.exists():
        raise FileNotFoundError(f"테스트 데이터가 없습니다: {TEST_PATH}")

    df = pd.read_csv(TEST_PATH)
    df["category"] = df["category"].map(normalize_category)

    results = {
        "category": evaluate_task("category", "category", LABEL_TO_ID, df),
        "urgency": evaluate_task("urgency", "urgency", URGENCY_TO_ID, df),
    }
    (REPORT_DIR / "multitask_metrics.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
