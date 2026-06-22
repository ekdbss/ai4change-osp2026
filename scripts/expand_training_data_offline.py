from __future__ import annotations

import argparse
import csv
import sys
from itertools import product
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from src.ai.label_map import LABEL_TO_ID, normalize_category


DATA_PATH = ROOT_DIR / "data/raw/generated_complaints.csv"

CATEGORY_BANKS = {
    "수업/학습 문제": {
        "subjects": ["수업 설명", "과제 안내", "평가 기준", "보충 학습", "수업 진도", "질문 응답", "온라인 과제", "준비물 안내"],
        "situations": [
            "학생이 내용을 충분히 이해하기 어려웠다고 이야기했습니다",
            "가정에서 확인하기에 안내 내용이 다소 부족했습니다",
            "학생마다 이해 정도의 차이가 커 보였습니다",
            "공지된 내용과 실제 진행 방식이 달라 혼란이 있었습니다",
            "학습 계획을 세우기 위해 추가 설명이 필요합니다",
            "수업 후 복습 과정에서 기준을 확인하기 어려웠습니다",
        ],
        "requests": [
            "관련 내용을 다시 안내해 주시기 바랍니다",
            "학생들이 이해할 수 있도록 보충 설명을 부탁드립니다",
            "가정에서도 확인할 수 있는 기준을 공유해 주시면 좋겠습니다",
            "향후 같은 혼란이 없도록 안내 방식을 점검해 주시기 바랍니다",
        ],
    },
    "교사 태도/행동": {
        "subjects": ["상담 과정", "지도 표현", "학생 응대", "학급 안내", "피드백 방식", "생활 지도", "수업 중 발언", "학부모 소통"],
        "situations": [
            "학생이 상황을 부담스럽게 받아들였다고 말했습니다",
            "가정에서 듣기에 표현의 의도가 충분히 전달되지 않은 것 같습니다",
            "학생이 자신이 존중받지 못했다고 느낀 부분이 있었습니다",
            "안내 과정에서 오해가 생길 수 있는 표현이 있었다고 생각합니다",
            "학생의 입장에서 설명이 조금 더 필요해 보였습니다",
            "상황을 정확히 확인하고 싶은 부분이 있습니다",
        ],
        "requests": [
            "사실관계를 확인한 뒤 필요한 안내를 부탁드립니다",
            "학생이 안정적으로 생활할 수 있도록 지도 방식을 검토해 주시기 바랍니다",
            "관련 상황에 대해 학교의 설명을 듣고 싶습니다",
            "향후 소통 과정에서 학생이 위축되지 않도록 살펴봐 주시기 바랍니다",
        ],
    },
    "시설/환경": {
        "subjects": ["교실 냉난방", "화장실 청결", "복도 조명", "책걸상 상태", "운동장 시설", "급수대 관리", "창문 안전", "실내 공기"],
        "situations": [
            "학생들이 이용하기에 불편함이 있다는 이야기를 들었습니다",
            "수업과 학교생활에 지장이 있을 수 있어 보입니다",
            "점검이 필요한 상태로 보여 걱정됩니다",
            "여러 학생이 함께 사용하는 공간이라 관리가 필요합니다",
            "최근 상태가 나빠졌다는 이야기가 있었습니다",
            "안전과 위생 측면에서 확인이 필요합니다",
        ],
        "requests": [
            "시설 상태를 점검하고 필요한 조치를 부탁드립니다",
            "조치 예정 시점을 안내해 주시면 감사하겠습니다",
            "학생들이 안전하게 이용할 수 있도록 확인해 주시기 바랍니다",
            "불편이 계속되지 않도록 관리 계획을 검토해 주시기 바랍니다",
        ],
    },
    "급식": {
        "subjects": ["급식 온도", "식단 안내", "알레르기 표시", "배식 과정", "음식 위생", "반찬 구성", "우유 제공", "급식실 운영"],
        "situations": [
            "학생이 식사 과정에서 불편함을 느꼈다고 말했습니다",
            "가정에서 확인하기에 안내가 조금 더 필요해 보입니다",
            "학생 건강과 관련될 수 있어 확인을 요청드립니다",
            "제공 방식에 대해 궁금한 부분이 있습니다",
            "여러 학생에게 영향을 줄 수 있는 사안으로 보입니다",
            "최근 반복적으로 비슷한 이야기가 들리고 있습니다",
        ],
        "requests": [
            "급식 운영 기준과 확인 결과를 안내해 주시기 바랍니다",
            "학생들이 안심하고 식사할 수 있도록 점검을 부탁드립니다",
            "필요한 경우 가정에도 관련 내용을 공유해 주시면 좋겠습니다",
            "재발 방지를 위한 관리 방안을 검토해 주시기 바랍니다",
        ],
    },
    "생활지도/안전": {
        "subjects": ["등하교 안전", "쉬는 시간 지도", "교내 이동", "운동장 이용", "친구 관계", "학교폭력 예방", "통학로 상황", "안전 교육"],
        "situations": [
            "학생이 불안함을 느낀 상황이 있었다고 말했습니다",
            "안전사고로 이어질 가능성이 있어 걱정됩니다",
            "학생들 사이의 관계를 조금 더 살펴볼 필요가 있어 보입니다",
            "지도 공백이 생기지 않도록 확인이 필요합니다",
            "비슷한 상황이 반복될까 우려됩니다",
            "학교 차원의 예방 안내가 필요해 보입니다",
        ],
        "requests": [
            "관련 상황을 확인하고 필요한 생활지도를 부탁드립니다",
            "학생 안전을 위해 지도 계획을 점검해 주시기 바랍니다",
            "가정에서도 함께 지도할 수 있도록 안내를 요청드립니다",
            "재발 방지를 위한 조치와 확인 결과를 알려주시기 바랍니다",
        ],
    },
    "기타": {
        "subjects": ["학교 행사", "가정통신문", "방과후 과정", "상담 일정", "행정 안내", "체험학습 절차", "준비물 공지", "학교 운영"],
        "situations": [
            "가정에서 확인해야 할 내용이 명확하지 않았습니다",
            "안내된 절차에 대해 추가 설명이 필요합니다",
            "일정과 준비 사항을 다시 확인하고 싶습니다",
            "학부모 입장에서 궁금한 부분이 남아 있습니다",
            "공지 내용만으로는 판단하기 어려운 점이 있습니다",
            "학교 운영 방식에 대해 문의드릴 부분이 있습니다",
        ],
        "requests": [
            "관련 기준과 절차를 안내해 주시기 바랍니다",
            "가정에서도 확인할 수 있도록 추가 공지를 부탁드립니다",
            "담당 부서에서 확인 후 답변해 주시면 감사하겠습니다",
            "혼란이 없도록 안내 내용을 보완해 주시기 바랍니다",
        ],
    },
}


def load_rows(path: Path) -> list[dict]:
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


def deduplicate(rows: list[dict]) -> list[dict]:
    unique_rows = []
    seen = set()
    for row in rows:
        text = str(row.get("text", "")).strip()
        category = normalize_category(row.get("category") or "")
        if not text or category not in LABEL_TO_ID or text in seen:
            continue
        seen.add(text)
        unique_rows.append({"text": text, "category": category})
    return unique_rows


def generate_category_rows(category: str, target_count: int, existing_rows: list[dict]) -> list[dict]:
    bank = CATEGORY_BANKS[category]
    rows = [row for row in existing_rows if row["category"] == category]
    seen = {row["text"] for row in rows}

    for subject, situation, request in product(bank["subjects"], bank["situations"], bank["requests"]):
        if len(rows) >= target_count:
            break
        text = f"{subject}와 관련해 {situation}. {request}"
        if text not in seen:
            rows.append({"text": text, "category": category})
            seen.add(text)

    return rows[:target_count]


def save_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["text", "category"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-per-label", type=int, default=200)
    args = parser.parse_args()

    existing_rows = deduplicate(load_rows(DATA_PATH))
    expanded_rows = []
    for category in LABEL_TO_ID:
        expanded_rows.extend(generate_category_rows(category, args.target_per_label, existing_rows))

    expanded_rows = deduplicate(expanded_rows)
    save_rows(DATA_PATH, expanded_rows)

    print(f"saved: {DATA_PATH} rows={len(expanded_rows)}")
    for category in LABEL_TO_ID:
        count = sum(1 for row in expanded_rows if row["category"] == category)
        print(f"{category}: {count}")


if __name__ == "__main__":
    main()
