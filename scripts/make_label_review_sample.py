from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from src.ai.label_map import LABEL_TO_ID, normalize_category


DEFAULT_INPUT_PATH = ROOT_DIR / "data/raw/generated_complaints.csv"
DEFAULT_OUTPUT_PATH = ROOT_DIR / "data/review/label_review_sample_300.csv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--per-category", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"데이터셋을 찾을 수 없습니다: {args.input}")

    df = pd.read_csv(args.input)
    category_column = "category" if "category" in df.columns else "label"
    if "text" not in df.columns or category_column not in df.columns:
        raise ValueError("입력 CSV에는 text와 category 또는 label 컬럼이 필요합니다.")

    df = df[["text", category_column]].copy()
    df.columns = ["text", "current_category"]
    df["text"] = df["text"].astype(str).str.strip()
    df["current_category"] = df["current_category"].map(normalize_category)
    df = df[df["text"].ne("") & df["current_category"].isin(LABEL_TO_ID)]

    samples = []
    for category in LABEL_TO_ID:
        category_df = df[df["current_category"] == category]
        if len(category_df) < args.per_category:
            raise ValueError(f"{category} 데이터가 {args.per_category}건보다 적습니다.")
        samples.append(category_df.sample(args.per_category, random_state=args.seed))

    review_df = pd.concat(samples, ignore_index=True)
    review_df = review_df.sample(frac=1, random_state=args.seed).reset_index(drop=True)
    review_df.insert(0, "review_id", range(1, len(review_df) + 1))
    review_df["review_category"] = ""
    review_df["review_urgency"] = ""
    review_df["review_note"] = ""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    review_df.to_csv(args.output, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)

    print(f"saved: {args.output}")
    print(f"rows: {len(review_df)}")
    print(review_df["current_category"].value_counts().reindex(LABEL_TO_ID.keys()).to_string())


if __name__ == "__main__":
    main()
