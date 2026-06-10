from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments

from dataset import ComplaintDataset


LABEL_TO_ID = {
    "수업/학습 문제": 0,
    "교사 태도/행동": 1,
    "시설/환경": 2,
    "급식": 3,
    "생활지도/안전": 4,
    "기타": 5,
}


BASE_MODEL = "skt/kobert-base-v1"
DATA_PATH = Path("data/raw/generated_complaints.csv")
OUTPUT_DIR = Path("model/saved_model")


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = logits.argmax(axis=-1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels,
        predictions,
        average="weighted",
        zero_division=0,
    )
    accuracy = accuracy_score(labels, predictions)
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"학습 데이터가 없습니다: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    if set(df.columns) != {"text", "label"}:
        raise ValueError("CSV 컬럼은 반드시 text,label 이어야 합니다.")

    df["label_id"] = df["label"].map(LABEL_TO_ID)
    if df["label_id"].isna().any():
        invalid = df[df["label_id"].isna()]["label"].unique()
        raise ValueError(f"정의되지 않은 라벨이 있습니다: {invalid}")

    train_df, temp_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df["label_id"],
    )
    valid_df, test_df = train_test_split(
        temp_df,
        test_size=0.5,
        random_state=42,
        stratify=temp_df["label_id"],
    )

    Path("data/processed").mkdir(parents=True, exist_ok=True)
    train_df[["text", "label"]].to_csv("data/processed/train.csv", index=False)
    valid_df[["text", "label"]].to_csv("data/processed/valid.csv", index=False)
    test_df[["text", "label"]].to_csv("data/processed/test.csv", index=False)

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL,
        num_labels=len(LABEL_TO_ID),
        id2label={value: key for key, value in LABEL_TO_ID.items()},
        label2id=LABEL_TO_ID,
    )

    train_dataset = ComplaintDataset(
        train_df["text"].tolist(),
        train_df["label_id"].astype(int).tolist(),
        tokenizer,
    )
    valid_dataset = ComplaintDataset(
        valid_df["text"].tolist(),
        valid_df["label_id"].astype(int).tolist(),
        tokenizer,
    )

    training_args = TrainingArguments(
        output_dir="model/checkpoints",
        evaluation_strategy="epoch",
        save_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=4,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_dir="reports/logs",
        logging_steps=20,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=valid_dataset,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )

    trainer.train()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))
    (OUTPUT_DIR / "label_map.json").write_text(
        json.dumps(LABEL_TO_ID, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

