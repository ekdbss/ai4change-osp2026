from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import google.generativeai as genai


LABELS = [
    "수업/학습 문제",
    "교사 태도/행동",
    "시설/환경",
    "급식",
    "생활지도/안전",
    "기타",
]

PROMPT_TEMPLATE = """
너는 한국 학교 민원 데이터셋 생성 전문가다.

목표:
KoBERT 기반 학교 민원 자동 분류 모델 학습용 Synthetic Data를 생성한다.

출력 형식:
반드시 JSON 배열만 출력한다.
각 항목은 아래 형식을 따른다.

[
  {{"text": "민원 문장", "label": "{label}"}}
]

생성 조건:
- label은 반드시 "{label}"만 사용한다.
- 지금은 "{label}" 라벨 데이터만 {count}개 생성한다.
- 문장은 실제 학부모 민원처럼 자연스럽게 작성한다.
- 개인정보, 학생 이름, 교사 이름, 학교 이름은 넣지 않는다.
- 욕설, 비방, 명예훼손 표현은 제외한다.
- 감정 강도는 낮음/보통/강함을 섞는다.
- 같은 표현을 반복하지 않는다.
- 한 문장은 20자 이상 120자 이하로 작성한다.
- 라벨과 무관한 문장은 생성하지 않는다.
- 설명 문장 없이 JSON 배열만 출력한다.
""".strip()


def parse_json_array(raw_text: str) -> list[dict]:
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned)


def main() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 필요합니다.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    rows = []
    for label in LABELS:
        prompt = PROMPT_TEMPLATE.format(label=label, count=200)
        response = model.generate_content(prompt)
        items = parse_json_array(response.text)
        rows.extend({"text": item["text"], "label": label} for item in items)

    unique_rows = []
    seen = set()
    for row in rows:
        if row["text"] not in seen:
            seen.add(row["text"])
            unique_rows.append(row)

    output_path = Path("data/raw/generated_complaints.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["text", "label"])
        writer.writeheader()
        writer.writerows(unique_rows)

    print(f"saved: {output_path} rows={len(unique_rows)}")


if __name__ == "__main__":
    main()

