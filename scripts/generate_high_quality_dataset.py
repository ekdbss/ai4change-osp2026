from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from src.ai.label_map import LABEL_TO_ID, normalize_category


load_dotenv(ROOT_DIR / ".env")

DEFAULT_INPUT_PATH = ROOT_DIR / "data/raw/generated_complaints_reviewed.csv"
DEFAULT_OUTPUT_PATH = ROOT_DIR / "data/raw/generated_complaints_hq_1800.csv"

VALID_URGENCIES = {"낮음", "보통", "높음"}
URGENCY_DISTRIBUTION = {
    "낮음": 0.25,
    "보통": 0.50,
    "높음": 0.25,
}

PROMPT_TEMPLATE = """
너는 한국 학교 민원 데이터셋을 만드는 NLP 데이터 라벨링 전문가다.

목표:
KoBERT 기반 학교 민원 자동 분류 모델 학습용 synthetic data를 생성한다.

생성 대상 카테고리:
{category}

생성 개수:
{count}개

긴급도 목표 개수:
- 낮음: {low_count}개
- 보통: {normal_count}개
- 높음: {high_count}개

반드시 아래 JSON 배열만 출력하라.
설명, 마크다운, 코드블록은 출력하지 않는다.

[
  {{
    "text": "민원 문장",
    "category": "{category}",
    "urgency": "낮음|보통|높음"
  }}
]

공통 생성 조건:
- category는 반드시 "{category}"만 사용한다.
- text는 실제 학부모가 학교에 남기는 민원처럼 자연스럽게 작성한다.
- 개인정보, 학교명, 교사명, 학생명, 전화번호, 주소는 넣지 않는다.
- 욕설, 명예훼손, 과도한 위협 표현은 넣지 않는다.
- 한 문장은 35자 이상 180자 이하로 작성한다.
- 같은 문장 구조를 반복하지 않는다.
- 같은 단어 조합을 과도하게 반복하지 않는다.
- 단순 키워드 나열이 아니라 상황과 요청이 모두 포함되게 작성한다.
- 감정 표현은 낮음, 보통, 강함이 섞이되 학교가 접수 가능한 표현이어야 한다.
- 기존 예시와 의미 또는 문장 구조가 지나치게 비슷한 문장은 만들지 않는다.

긴급도 기준:
- 높음: 안전, 건강, 폭력, 학대, 인권침해, 사고 위험, 식중독, 알레르기, 시설 위험이 포함된 사안
- 보통: 수업, 평가, 교사 응대, 생활지도 방식 등 일반 불만이나 확인 요청
- 낮음: 단순 문의, 건의, 개선 요청, 일정/절차 확인

카테고리 라벨 기준:
- 수업/학습 문제: 수업 내용, 과제, 평가, 시험, 진도, 설명 부족, 보충학습, 준비물 안내가 핵심이다.
- 교사 태도/행동: 교사의 말투, 상담 태도, 차별, 학생 응대, 지도 방식, 학부모 소통 방식이 핵심이다.
- 시설/환경: 교실, 화장실, 냉난방, 조명, 책걸상, 창문, 운동장, 공사, 소음, 위생, 공기질 등 물리적 환경이 핵심이다.
- 급식: 급식 식단, 음식 온도, 위생, 알레르기 표시, 배식, 식중독 우려, 우유 제공 등 급식 운영이 핵심이다.
- 생활지도/안전: 학교폭력, 따돌림, 괴롭힘, 등하교 안전, 사고 위험, 쉬는 시간 지도, 운동장 안전, 생활지도 공백이 핵심이다.
- 기타: 행사, 일정, 행정 절차, 서류, 가정통신문, 방과후 과정, 상담 일정, 학교 운영 문의 등 다른 카테고리에 명확히 속하지 않는 사안이다.

중요한 경계 사례:
- "선생님이 숙제를 많이 내주셨다"는 수업/학습 문제이다.
- "선생님 말투 때문에 학생이 위축되었다"는 교사 태도/행동이다.
- "급식실 바닥이 미끄러워 넘어질 위험이 있다"는 생활지도/안전 또는 시설/환경 중 위험성이 핵심이면 높음으로 표시한다.
- "알레르기 표시가 부족하다"는 급식이며 긴급도는 높음일 수 있다.
- "행사 일정 안내가 부족하다"는 기타이다.

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


def load_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []

    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            text = str(row.get("text", "")).strip()
            category = normalize_category(row.get("category") or row.get("label") or "")
            urgency = str(row.get("urgency", "")).strip()
            if text and category in LABEL_TO_ID:
                rows.append(
                    {
                        "text": text,
                        "category": category,
                        "urgency": urgency if urgency in VALID_URGENCIES else "",
                        "source": row.get("source") or ("reviewed" if row.get("reviewed") else "base"),
                    }
                )
    return rows


def deduplicate_rows(rows: list[dict]) -> list[dict]:
    unique_rows = []
    seen = set()
    for row in rows:
        text = str(row.get("text", "")).strip()
        category = normalize_category(row.get("category") or "")
        urgency = str(row.get("urgency", "")).strip()
        if not text or category not in LABEL_TO_ID or urgency not in VALID_URGENCIES or text in seen:
            continue
        seen.add(text)
        unique_rows.append(
            {
                "text": text,
                "category": category,
                "urgency": urgency,
                "source": row.get("source") or "base",
            }
        )
    return unique_rows


def save_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["text", "category", "urgency", "source"])
        writer.writeheader()
        writer.writerows(rows)


def trim_category_to_target(rows: list[dict], category: str, target_count: int) -> list[dict]:
    category_rows = [row for row in rows if row["category"] == category]
    if len(category_rows) <= target_count:
        return rows

    kept_category_rows = category_rows[:target_count]
    non_category_rows = [row for row in rows if row["category"] != category]
    return [*non_category_rows, *kept_category_rows]


def build_examples(rows: list[dict], category: str, limit: int = 12) -> str:
    examples = [row for row in rows if row["category"] == category][-limit:]
    if not examples:
        return "- 없음"
    return "\n".join(
        f"- [{row['urgency']}] {row['text']}"
        for row in examples
    )


def urgency_targets(count: int) -> dict[str, int]:
    low_count = round(count * URGENCY_DISTRIBUTION["낮음"])
    high_count = round(count * URGENCY_DISTRIBUTION["높음"])
    normal_count = count - low_count - high_count
    return {
        "낮음": low_count,
        "보통": normal_count,
        "높음": high_count,
    }


def generate_rows(model, category: str, count: int, rows: list[dict]) -> list[dict]:
    targets = urgency_targets(count)
    prompt = PROMPT_TEMPLATE.format(
        category=category,
        count=count,
        low_count=targets["낮음"],
        normal_count=targets["보통"],
        high_count=targets["높음"],
        examples=build_examples(rows, category),
    )
    response = model.generate_content(prompt)
    items = parse_json_array(response.text)

    generated_rows = []
    for item in items:
        text = str(item.get("text", "")).strip()
        item_category = normalize_category(item.get("category") or category)
        urgency = str(item.get("urgency", "")).strip()
        if text and item_category == category and urgency in VALID_URGENCIES:
            generated_rows.append(
                {
                    "text": text,
                    "category": item_category,
                    "urgency": urgency,
                    "source": "gemini_hq",
                }
            )
    return generated_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--target-per-category", type=int, default=300)
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--max-attempts-per-category", type=int, default=6)
    parser.add_argument("--max-quota-retries", type=int, default=2)
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--normalize-only", action="store_true")
    args = parser.parse_args()

    if args.resume and args.output.exists():
        rows = deduplicate_rows(load_rows(args.output))
    else:
        rows = deduplicate_rows(load_rows(args.input))
        save_rows(args.output, rows)

    for category in LABEL_TO_ID:
        rows = trim_category_to_target(rows, category, args.target_per_category)
    save_rows(args.output, rows)

    if args.normalize_only:
        print(f"normalized: {args.output} rows={len(rows)}")
        return

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 필요합니다.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    for category in LABEL_TO_ID:
        attempts = 0
        while attempts < args.max_attempts_per_category:
            current_count = sum(1 for row in rows if row["category"] == category)
            missing_count = args.target_per_category - current_count
            if missing_count <= 0:
                break

            batch_count = min(args.batch_size, missing_count)
            for quota_retry in range(args.max_quota_retries + 1):
                try:
                    generated = generate_rows(model, category, batch_count, rows)
                    break
                except ResourceExhausted as exc:
                    save_rows(args.output, rows)
                    if quota_retry >= args.max_quota_retries:
                        print("Gemini 요청 한도에 도달했습니다. 현재까지 생성된 결과를 저장했습니다.")
                        print(f"이어 하려면 다음 명령을 다시 실행하세요: python scripts/generate_high_quality_dataset.py --resume")
                        raise exc
                    wait_seconds = max(args.sleep_seconds * 4, 30)
                    print(f"Gemini 요청 한도 대기 중입니다. {wait_seconds:.0f}초 뒤 재시도합니다.")
                    time.sleep(wait_seconds)
            else:
                generated = []

            rows = deduplicate_rows([*rows, *generated])
            rows = trim_category_to_target(rows, category, args.target_per_category)
            save_rows(args.output, rows)
            attempts += 1
            updated_count = sum(1 for row in rows if row["category"] == category)
            print(f"{category}: {current_count} -> {updated_count}")
            time.sleep(args.sleep_seconds)

    save_rows(args.output, rows)
    print(f"saved: {args.output} rows={len(rows)}")
    print("category counts")
    for category in LABEL_TO_ID:
        print(f"{category}: {sum(1 for row in rows if row['category'] == category)}")
    print("urgency counts")
    for urgency in ["낮음", "보통", "높음"]:
        print(f"{urgency}: {sum(1 for row in rows if row['urgency'] == urgency)}")


if __name__ == "__main__":
    main()
