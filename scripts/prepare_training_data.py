from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from src.ai.label_map import department_for_category, normalize_category


RAW_DATA_PATH = ROOT_DIR / "data/raw/generated_complaints.csv"
OUTPUT_PATH = ROOT_DIR / "data/raw/generated_complaints_multitask.csv"

HIGH_URGENCY_KEYWORDS = [
    "사고",
    "다쳤",
    "다칠",
    "위험",
    "안전",
    "폭력",
    "따돌림",
    "괴롭힘",
    "협박",
    "성희롱",
    "식중독",
    "알레르기",
    "응급",
    "병원",
    "파손",
    "이물질",
    "상한",
    "신고",
    "교육청",
]

LOW_URGENCY_KEYWORDS = [
    "문의",
    "궁금",
    "일정",
    "안내",
    "참고",
    "건의",
    "제안",
    "희망",
    "부탁",
    "조정",
]


def infer_urgency(text: str, category: str) -> str:
    normalized_text = str(text)

    if any(keyword in normalized_text for keyword in HIGH_URGENCY_KEYWORDS):
        return "높음"

    if category == "생활지도/안전":
        return "높음"

    if category in {"교사 태도/행동", "수업/학습 문제"}:
        return "보통"

    if any(keyword in normalized_text for keyword in LOW_URGENCY_KEYWORDS):
        return "낮음"

    return "보통"


def main() -> None:
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"원본 데이터셋을 찾을 수 없습니다: {RAW_DATA_PATH}")

    df = pd.read_csv(RAW_DATA_PATH)
    if "text" not in df.columns:
        raise ValueError("원본 데이터셋에는 text 컬럼이 필요합니다.")

    category_column = "category" if "category" in df.columns else "label"
    if category_column not in df.columns:
        raise ValueError("원본 데이터셋에는 category 또는 label 컬럼이 필요합니다.")

    prepared = pd.DataFrame()
    prepared["text"] = df["text"].astype(str).str.strip()
    prepared["category"] = df[category_column].map(normalize_category)
    prepared["urgency"] = prepared.apply(
        lambda row: infer_urgency(row["text"], row["category"]),
        axis=1,
    )
    prepared["department"] = prepared["category"].map(department_for_category)

    prepared.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"saved: {OUTPUT_PATH}")
    print(prepared[["category", "urgency"]].value_counts().sort_index())


if __name__ == "__main__":
    main()
