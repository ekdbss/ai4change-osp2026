from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from scripts.fill_label_review_defaults import infer_review_urgency
from src.ai.label_map import LABEL_TO_ID, normalize_category


DEFAULT_INPUT_PATH = ROOT_DIR / "data/raw/generated_complaints.csv"
DEFAULT_REVIEW_PATH = ROOT_DIR / "data/review/label_review_sample_300.csv"
DEFAULT_OUTPUT_PATH = ROOT_DIR / "data/raw/generated_complaints_reviewed.csv"

VALID_URGENCIES = {"낮음", "보통", "높음"}


def clean_text(value) -> str:
    return str(value).strip()


def first_non_blank(*values) -> str:
    for value in values:
        if not pd.isna(value) and str(value).strip():
            return str(value).strip()
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"원본 데이터셋을 찾을 수 없습니다: {args.input}")
    if not args.review.exists():
        raise FileNotFoundError(f"검수 CSV를 찾을 수 없습니다: {args.review}")

    source_df = pd.read_csv(args.input)
    source_category_column = "category" if "category" in source_df.columns else "label"
    if "text" not in source_df.columns or source_category_column not in source_df.columns:
        raise ValueError("원본 CSV에는 text와 category 또는 label 컬럼이 필요합니다.")

    review_df = pd.read_csv(args.review)
    required_review_columns = {"text", "current_category", "review_category", "review_urgency"}
    missing_columns = required_review_columns - set(review_df.columns)
    if missing_columns:
        raise ValueError(f"검수 CSV에 필수 컬럼이 없습니다: {sorted(missing_columns)}")

    review_map = {}
    for _, row in review_df.iterrows():
        text = clean_text(row["text"])
        if not text:
            continue

        category = normalize_category(first_non_blank(row.get("review_category"), row.get("current_category")))
        urgency = first_non_blank(row.get("review_urgency"))
        if category not in LABEL_TO_ID:
            raise ValueError(f"정의되지 않은 검수 카테고리입니다: {category}")
        if urgency not in VALID_URGENCIES:
            raise ValueError(f"정의되지 않은 검수 긴급도입니다: {urgency}")

        review_map[text] = {
            "category": category,
            "urgency": urgency,
            "reviewed": True,
        }

    rows = []
    matched_count = 0
    for _, row in source_df.iterrows():
        text = clean_text(row["text"])
        original_category = normalize_category(row[source_category_column])
        if original_category not in LABEL_TO_ID:
            raise ValueError(f"정의되지 않은 원본 카테고리입니다: {original_category}")

        reviewed = review_map.get(text)
        if reviewed:
            matched_count += 1
            category = reviewed["category"]
            urgency = reviewed["urgency"]
            is_reviewed = True
        else:
            category = original_category
            urgency = infer_review_urgency(text, category)
            is_reviewed = False

        rows.append(
            {
                "text": text,
                "category": category,
                "urgency": urgency,
                "reviewed": is_reviewed,
            }
        )

    output_df = pd.DataFrame(rows).drop_duplicates(subset=["text"], keep="first")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(args.output, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)

    print(f"saved: {args.output}")
    print(f"rows: {len(output_df)}")
    print(f"review rows: {len(review_map)}")
    print(f"matched rows: {matched_count}")
    print("category counts")
    print(output_df["category"].value_counts().reindex(LABEL_TO_ID.keys(), fill_value=0).to_string())
    print("urgency counts")
    print(output_df["urgency"].value_counts().reindex(["낮음", "보통", "높음"], fill_value=0).to_string())


if __name__ == "__main__":
    main()
