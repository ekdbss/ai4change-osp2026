from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd


DEFAULT_REVIEW_PATH = Path("data/review/label_review_sample_300.csv")

HIGH_URGENCY_KEYWORDS = [
    "안전",
    "건강",
    "폭력",
    "학교폭력",
    "학대",
    "인권",
    "침해",
    "사고",
    "다쳤",
    "다침",
    "다칠",
    "부상",
    "병원",
    "응급",
    "위험",
    "식중독",
    "알레르기",
    "유통기한",
    "탈",
    "배탈",
    "복통",
    "설사",
    "변질",
    "곰팡이",
    "부패",
    "상한",
    "상했",
    "이물질",
    "파손",
    "균열",
    "깨진",
    "고장",
    "미끄",
    "화재",
    "전기",
    "감전",
    "난간",
    "창문",
    "괴롭힘",
    "따돌림",
    "협박",
    "성희롱",
]

LOW_URGENCY_KEYWORDS = [
    "문의",
    "궁금",
    "일정",
    "행사",
    "절차",
    "서류",
    "신청",
    "가정통신문",
    "방과후",
    "체험학습",
    "안내",
    "건의",
    "제안",
    "희망",
    "참고",
]

GENERAL_COMPLAINT_KEYWORDS = [
    "불편",
    "부족",
    "걱정",
    "문제",
    "어렵",
    "혼란",
    "반복",
    "상태",
    "점검",
    "조치",
    "위축",
    "스트레스",
]


def is_blank(value) -> bool:
    return pd.isna(value) or str(value).strip() == ""


def infer_review_urgency(text: str, category: str) -> str:
    if any(keyword in text for keyword in HIGH_URGENCY_KEYWORDS):
        return "높음"

    if category in {"수업/학습 문제", "교사 태도/행동"}:
        return "보통"

    if category == "기타":
        return "낮음"

    has_low_signal = any(keyword in text for keyword in LOW_URGENCY_KEYWORDS)
    has_complaint_signal = any(keyword in text for keyword in GENERAL_COMPLAINT_KEYWORDS)
    if has_low_signal and not has_complaint_signal:
        return "낮음"

    return "보통"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=DEFAULT_REVIEW_PATH)
    parser.add_argument("--overwrite-urgency", action="store_true")
    args = parser.parse_args()

    if not args.path.exists():
        raise FileNotFoundError(f"검수 CSV를 찾을 수 없습니다: {args.path}")

    df = pd.read_csv(args.path)
    required_columns = {"text", "current_category", "review_category", "review_urgency"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"필수 컬럼이 없습니다: {sorted(missing_columns)}")

    for column in ["review_category", "review_urgency", "review_note"]:
        df[column] = df[column].fillna("").astype(str)

    filled_category_count = 0
    filled_urgency_count = 0

    for index, row in df.iterrows():
        current_category = str(row["current_category"]).strip()
        if is_blank(row["review_category"]):
            df.at[index, "review_category"] = current_category
            filled_category_count += 1

        review_category = str(df.at[index, "review_category"]).strip()
        if args.overwrite_urgency or is_blank(row["review_urgency"]):
            df.at[index, "review_urgency"] = infer_review_urgency(str(row["text"]), review_category)
            filled_urgency_count += 1

    df.to_csv(args.path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)

    print(f"updated: {args.path}")
    print(f"filled review_category: {filled_category_count}")
    print(f"filled review_urgency: {filled_urgency_count}")
    print(df["review_category"].value_counts().to_string())
    print(df["review_urgency"].value_counts().to_string())


if __name__ == "__main__":
    main()
