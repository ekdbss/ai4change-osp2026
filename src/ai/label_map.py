LABEL_TO_ID = {
    "수업/학습 문제": 0,
    "교사 태도/행동": 1,
    "시설/환경": 2,
    "급식": 3,
    "생활지도/안전": 4,
    "기타": 5,
}

ID_TO_LABEL = {value: key for key, value in LABEL_TO_ID.items()}

RAW_CATEGORY_ALIASES = {
    "수업_학습": "수업/학습 문제",
    "수업/학습": "수업/학습 문제",
    "학습": "수업/학습 문제",
    "교사_태도": "교사 태도/행동",
    "교사 태도": "교사 태도/행동",
    "시설_환경": "시설/환경",
    "생활지도_안전": "생활지도/안전",
    "생활지도 안전": "생활지도/안전",
}

URGENCY_TO_ID = {
    "낮음": 0,
    "보통": 1,
    "높음": 2,
}

ID_TO_URGENCY = {value: key for key, value in URGENCY_TO_ID.items()}

DEPARTMENT_BY_CATEGORY = {
    "수업/학습 문제": "교무부",
    "교사 태도/행동": "교무부",
    "시설/환경": "시설관리",
    "급식": "급식실",
    "생활지도/안전": "생활안전부",
    "기타": "행정실",
}

PRIORITY_BY_URGENCY = {
    "높음": 1,
    "보통": 3,
    "낮음": 4,
}


def normalize_category(raw_category: str) -> str:
    value = str(raw_category).strip()
    return RAW_CATEGORY_ALIASES.get(value, value)


def department_for_category(category: str) -> str:
    return DEPARTMENT_BY_CATEGORY.get(category, "행정실")


def priority_for_urgency(urgency: str) -> int:
    return PRIORITY_BY_URGENCY.get(urgency, 3)
