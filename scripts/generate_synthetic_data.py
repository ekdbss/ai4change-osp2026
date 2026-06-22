from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from src.ai.label_map import LABEL_TO_ID, normalize_category


load_dotenv(ROOT_DIR / ".env")

LABELS = list(LABEL_TO_ID.keys())
DATA_PATH = ROOT_DIR / "data/raw/generated_complaints.csv"

PROMPT_TEMPLATE = """
너는 한국 학교 민원 데이터셋 생성 전문가다.

목표:
KoBERT 기반 학교 민원 자동 분류 모델 학습용 Synthetic Data를 생성한다.

출력 형식:
반드시 JSON 배열만 출력한다.
각 항목은 아래 형식을 따른다.

[
  {{"text": "민원 문장", "category": "{label}"}}
]

생성 조건:
- category는 반드시 "{label}"만 사용한다.
- 지금은 "{label}" 라벨 데이터만 {count}개 생성한다.
- 문장은 실제 학부모 민원처럼 자연스럽게 작성한다.
- 개인정보, 학생 이름, 교사 이름, 학교 이름은 넣지 않는다.
- 욕설, 비방, 명예훼손 표현은 제외한다.
- 감정 강도는 낮음/보통/강함을 섞는다.
- 같은 표현을 반복하지 않는다.
- 한 문장은 20자 이상 120자 이하로 작성한다.
- 라벨과 무관한 문장은 생성하지 않는다.
- 아래 기존 예시와 의미 또는 문장 구조가 지나치게 비슷한 문장은 만들지 않는다.
- 설명 문장 없이 JSON 배열만 출력한다.

기존 예시:
{examples}
""".strip()


def parse_json_array(raw_text: str) -> list[dict]:
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start >= 0 and end >= start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def load_existing_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []

    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            text = str(row.get("text", "")).strip()
            category = normalize_category(row.get("category") or row.get("label") or "")
            if text and category in LABEL_TO_ID:
                rows.append({"text": text, "category": category})
    return rows


def deduplicate_rows(rows: list[dict]) -> list[dict]:
    unique_rows = []
    seen = set()
    for row in rows:
        text = str(row.get("text", "")).strip()
        category = normalize_category(row.get("category") or row.get("label") or "")
        if not text or category not in LABEL_TO_ID or text in seen:
            continue
        seen.add(text)
        unique_rows.append({"text": text, "category": category})
    return unique_rows


def build_examples(rows: list[dict], label: str, limit: int = 10) -> str:
    examples = [row["text"] for row in rows if row["category"] == label][-limit:]
    if not examples:
        return "- 없음"
    return "\n".join(f"- {example}" for example in examples)


def generate_rows(model, label: str, count: int, existing_rows: list[dict]) -> list[dict]:
    prompt = PROMPT_TEMPLATE.format(
        label=label,
        count=count,
        examples=build_examples(existing_rows, label),
    )
    response = model.generate_content(prompt)
    items = parse_json_array(response.text)

    rows = []
    for item in items:
        text = str(item.get("text", "")).strip()
        category = normalize_category(item.get("category") or item.get("label") or label)
        if text and category == label:
            rows.append({"text": text, "category": category})
    return rows


def save_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["text", "category"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-per-label", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=40)
    parser.add_argument("--max-attempts-per-label", type=int, default=10)
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 필요합니다.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    rows = deduplicate_rows(load_existing_rows(DATA_PATH))
    for label in LABELS:
        attempts = 0
        while attempts < args.max_attempts_per_label:
            current_count = sum(1 for row in rows if row["category"] == label)
            missing_count = args.target_per_label - current_count
            if missing_count <= 0:
                break

            batch_count = min(args.batch_size, missing_count)
            generated = generate_rows(model, label, batch_count, rows)
            rows = deduplicate_rows([*rows, *generated])
            attempts += 1
            print(
                f"{label}: {current_count} -> "
                f"{sum(1 for row in rows if row['category'] == label)}"
            )

    save_rows(DATA_PATH, rows)

    print(f"saved: {DATA_PATH} rows={len(rows)}")
    counts = {label: sum(1 for row in rows if row["category"] == label) for label in LABELS}
    print(json.dumps(counts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
