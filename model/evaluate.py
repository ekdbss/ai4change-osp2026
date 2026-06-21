from __future__ import annotations

import json
from pathlib import Path

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


MODEL_DIR = Path("model/saved_model")
TEST_PATH = Path("data/processed/test.csv")
REPORT_DIR = Path("reports")


def main() -> None:
    if not MODEL_DIR.exists():
        raise FileNotFoundError(f"저장된 모델이 없습니다: {MODEL_DIR}")
    if not TEST_PATH.exists():
        raise FileNotFoundError(f"테스트 데이터가 없습니다: {TEST_PATH}")

    label_map = json.loads((MODEL_DIR / "label_map.json").read_text(encoding="utf-8"))
    id_to_label = {value: key for key, value in label_map.items()}

    tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
    model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_DIR))
    model.eval()

    df = pd.read_csv(TEST_PATH)
    true_ids = [label_map[label] for label in df["label"]]
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
    (REPORT_DIR / "classification_report.txt").write_text(report, encoding="utf-8")
    (REPORT_DIR / "metrics.json").write_text(
        json.dumps(
            {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1": f1,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    display = ConfusionMatrixDisplay(confusion_matrix=matrix, display_labels=target_names)
    display.plot(cmap="Blues", xticks_rotation=45)
    plt.tight_layout()
    plt.savefig(REPORT_DIR / "confusion_matrix.png", dpi=160)


if __name__ == "__main__":
    main()

