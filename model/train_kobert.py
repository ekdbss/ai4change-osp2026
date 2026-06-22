from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from dataset import ComplaintDataset
from src.ai.label_map import LABEL_TO_ID, URGENCY_TO_ID, department_for_category, normalize_category
from scripts.prepare_training_data import infer_urgency


BASE_MODEL = "skt/kobert-base-v1"
DATA_PATH = ROOT_DIR / "data/raw/generated_complaints_multitask.csv"
FALLBACK_DATA_PATH = ROOT_DIR / "data/raw/generated_complaints.csv"
OUTPUT_DIR = ROOT_DIR / "model/saved_model"
CHECKPOINT_DIR = ROOT_DIR / "model/checkpoints"
PROCESSED_DIR = ROOT_DIR / "data/processed"


def compute_metrics(eval_pred):
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support

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


def load_training_dataframe() -> pd.DataFrame:
    data_path = DATA_PATH if DATA_PATH.exists() else FALLBACK_DATA_PATH
    if not data_path.exists():
        raise FileNotFoundError(f"학습 데이터가 없습니다: {data_path}")

    df = pd.read_csv(data_path)
    if "text" not in df.columns:
        raise ValueError("CSV 컬럼에는 text가 필요합니다.")

    if "category" not in df.columns and "label" in df.columns:
        df["category"] = df["label"]
    if "category" not in df.columns:
        raise ValueError("CSV 컬럼에는 category 또는 label이 필요합니다.")

    df["text"] = df["text"].astype(str).str.strip()
    df["category"] = df["category"].map(normalize_category)

    invalid_categories = sorted(set(df["category"]) - set(LABEL_TO_ID))
    if invalid_categories:
        raise ValueError(f"정의되지 않은 카테고리가 있습니다: {invalid_categories}")

    if "urgency" not in df.columns:
        df["urgency"] = df.apply(lambda row: infer_urgency(row["text"], row["category"]), axis=1)

    invalid_urgencies = sorted(set(df["urgency"]) - set(URGENCY_TO_ID))
    if invalid_urgencies:
        raise ValueError(f"정의되지 않은 긴급도가 있습니다: {invalid_urgencies}")

    if "department" not in df.columns:
        df["department"] = df["category"].map(department_for_category)

    df["category_id"] = df["category"].map(LABEL_TO_ID).astype(int)
    df["urgency_id"] = df["urgency"].map(URGENCY_TO_ID).astype(int)
    return df


def split_and_save(
    df: pd.DataFrame,
    max_train_samples: int | None = None,
    max_valid_samples: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    from sklearn.model_selection import train_test_split

    stratify_key = df["category"].astype(str) + "_" + df["urgency"].astype(str)
    if stratify_key.value_counts().min() < 2:
        stratify_key = df["category_id"]

    train_df, temp_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=stratify_key,
    )

    temp_stratify = temp_df["category"].astype(str) + "_" + temp_df["urgency"].astype(str)
    if temp_stratify.value_counts().min() < 2:
        temp_stratify = temp_df["category_id"]

    valid_df, test_df = train_test_split(
        temp_df,
        test_size=0.5,
        random_state=42,
        stratify=temp_stratify,
    )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    columns = ["text", "category", "urgency", "department"]
    train_df[columns].to_csv(PROCESSED_DIR / "train.csv", index=False, encoding="utf-8-sig")
    valid_df[columns].to_csv(PROCESSED_DIR / "valid.csv", index=False, encoding="utf-8-sig")
    test_df[columns].to_csv(PROCESSED_DIR / "test.csv", index=False, encoding="utf-8-sig")

    if max_train_samples:
        train_df = _sample_balanced(train_df, max_train_samples)
    if max_valid_samples:
        valid_df = _sample_balanced(valid_df, max_valid_samples)

    return train_df, valid_df, test_df


def _sample_balanced(df: pd.DataFrame, sample_count: int) -> pd.DataFrame:
    if sample_count >= len(df):
        return df
    return (
        df.groupby("category", group_keys=False)
        .apply(lambda group: group.sample(min(len(group), max(1, sample_count // 6)), random_state=42))
        .sample(frac=1, random_state=42)
        .reset_index(drop=True)
    )


def train_task(
    task_name: str,
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    label_column: str,
    label_map: dict[str, int],
    tokenizer,
    epochs: float,
    batch_size: int,
    max_length: int,
    freeze_base: bool,
) -> None:
    from transformers import AutoModelForSequenceClassification, Trainer, TrainingArguments

    id_to_label = {value: key for key, value in label_map.items()}
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL,
        num_labels=len(label_map),
        id2label=id_to_label,
        label2id=label_map,
    )
    if freeze_base:
        for name, parameter in model.named_parameters():
            parameter.requires_grad = name.startswith("classifier")

    train_dataset = ComplaintDataset(
        train_df["text"].tolist(),
        train_df[label_column].astype(int).tolist(),
        tokenizer,
        max_length=max_length,
    )
    valid_dataset = ComplaintDataset(
        valid_df["text"].tolist(),
        valid_df[label_column].astype(int).tolist(),
        tokenizer,
        max_length=max_length,
    )

    training_args = TrainingArguments(
        output_dir=str(CHECKPOINT_DIR / task_name),
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        num_train_epochs=epochs,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_dir=str(ROOT_DIR / "reports/logs" / task_name),
        logging_steps=20,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=valid_dataset,
        processing_class=tokenizer,
        compute_metrics=compute_metrics,
    )

    trainer.train()

    task_output_dir = OUTPUT_DIR / task_name
    task_output_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(task_output_dir))
    tokenizer.save_pretrained(str(task_output_dir))
    (task_output_dir / "label_map.json").write_text(
        json.dumps(label_map, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    from transformers import AutoTokenizer

    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=float, default=4)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-train-samples", type=int, default=0)
    parser.add_argument("--max-valid-samples", type=int, default=0)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--freeze-base", action="store_true")
    parser.add_argument(
        "--tasks",
        nargs="+",
        choices=["category", "urgency"],
        default=["category", "urgency"],
    )
    args = parser.parse_args()

    df = load_training_dataframe()
    train_df, valid_df, _ = split_and_save(
        df,
        max_train_samples=args.max_train_samples or None,
        max_valid_samples=args.max_valid_samples or None,
    )

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    if "category" in args.tasks:
        train_task(
            "category",
            train_df,
            valid_df,
            "category_id",
            LABEL_TO_ID,
            tokenizer,
            args.epochs,
            args.batch_size,
            args.max_length,
            args.freeze_base,
        )
    if "urgency" in args.tasks:
        train_task(
            "urgency",
            train_df,
            valid_df,
            "urgency_id",
            URGENCY_TO_ID,
            tokenizer,
            args.epochs,
            args.batch_size,
            args.max_length,
            args.freeze_base,
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "task_config.json").write_text(
        json.dumps(
            {
                "base_model": BASE_MODEL,
                "tasks": {
                    "category": {
                        "path": "category",
                        "labels": LABEL_TO_ID,
                    },
                    "urgency": {
                        "path": "urgency",
                        "labels": URGENCY_TO_ID,
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
