from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.ai.label_map import (
    ID_TO_LABEL,
    ID_TO_URGENCY,
    department_for_category,
    priority_for_urgency,
)
from src.ai.model_artifacts import ensure_model_artifacts, has_saved_model, task_model_path


@dataclass
class PredictionResult:
    category: str
    confidence: float
    urgency: str
    urgency_confidence: float
    recommended_department: str
    priority_level: int
    model_available: bool
    category_model_available: bool
    urgency_model_available: bool
    top_categories: list[dict]
    load_errors: list[str]

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "confidence": self.confidence,
            "urgency": self.urgency,
            "urgency_confidence": self.urgency_confidence,
            "recommended_department": self.recommended_department,
            "priority_level": self.priority_level,
            "model_available": self.model_available,
            "category_model_available": self.category_model_available,
            "urgency_model_available": self.urgency_model_available,
            "top_categories": self.top_categories,
            "load_errors": self.load_errors,
        }


class KeywordFallbackClassifier:
    """Development fallback used only until the fine-tuned KoBERT models exist."""

    CATEGORY_RULES = {
        "급식": ["급식", "반찬", "식단", "알레르기", "우유", "음식", "위생", "배식", "식중독"],
        "시설/환경": ["교실", "화장실", "에어컨", "난방", "시설", "환경", "소음", "공사", "파손"],
        "생활지도/안전": ["폭력", "따돌림", "안전", "등교", "하교", "운동장", "사고", "생활지도"],
        "교사 태도/행동": ["선생님", "교사", "담임", "말투", "무시", "차별", "상담", "태도"],
        "수업/학습 문제": ["수업", "숙제", "과제", "시험", "평가", "진도", "설명", "학습"],
    }
    HIGH_URGENCY_WORDS = [
        "사고",
        "다쳤",
        "다칠",
        "위험",
        "폭력",
        "따돌림",
        "협박",
        "식중독",
        "알레르기",
        "상한",
        "파손",
        "신고",
        "교육청",
    ]
    LOW_URGENCY_WORDS = ["문의", "궁금", "일정", "안내", "참고", "건의", "제안"]

    def predict(self, text: str) -> PredictionResult:
        scores = {label: 0 for label in ID_TO_LABEL.values()}
        for label, words in self.CATEGORY_RULES.items():
            scores[label] = sum(1 for word in words if word in text)

        sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        best_label = sorted_scores[0][0]
        if scores[best_label] == 0:
            best_label = "기타"

        urgency = self._infer_urgency(text, best_label)
        top_categories = [
            {
                "category": label,
                "confidence": 0.50 if index == 0 and label == best_label else 0.0,
            }
            for index, (label, _) in enumerate(sorted_scores[:3])
        ]

        return PredictionResult(
            category=best_label,
            confidence=0.50,
            urgency=urgency,
            urgency_confidence=0.50,
            recommended_department=department_for_category(best_label),
            priority_level=priority_for_urgency(urgency),
            model_available=False,
            category_model_available=False,
            urgency_model_available=False,
            top_categories=top_categories,
            load_errors=[],
        )

    def _infer_urgency(self, text: str, category: str) -> str:
        if any(word in text for word in self.HIGH_URGENCY_WORDS):
            return "높음"
        if category == "생활지도/안전":
            return "높음"
        if any(word in text for word in self.LOW_URGENCY_WORDS):
            return "낮음"
        return "보통"


class KoBERTPredictor:
    def __init__(self, model_path: str, max_length: int = 128):
        self.model_path = Path(model_path)
        self.max_length = max_length
        self.fallback = KeywordFallbackClassifier()
        self.torch = None
        self.device = None
        self.category_model = None
        self.category_tokenizer = None
        self.urgency_model = None
        self.urgency_tokenizer = None
        self.category_id_to_label = ID_TO_LABEL
        self.urgency_id_to_label = ID_TO_URGENCY
        self.load_errors = []

        artifact_status = ensure_model_artifacts(self.model_path)
        if artifact_status.get("download_error"):
            self.load_errors.append(artifact_status["download_error"])

        self.category_model_path = self._resolve_task_path("category")
        self.urgency_model_path = self._resolve_task_path("urgency")
        self.category_model_available = has_saved_model(self.category_model_path)
        self.urgency_model_available = has_saved_model(self.urgency_model_path)
        self.model_available = self.category_model_available or self.urgency_model_available

        if self.model_available:
            try:
                import torch
                from transformers import AutoModelForSequenceClassification, AutoTokenizer

                self.torch = torch
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

                if self.category_model_available:
                    try:
                        self.category_tokenizer = AutoTokenizer.from_pretrained(str(self.category_model_path))
                        self.category_model = AutoModelForSequenceClassification.from_pretrained(
                            str(self.category_model_path)
                        )
                        self.category_model.to(self.device)
                        self.category_model.eval()
                        self.category_id_to_label = self._load_id_to_label(self.category_model_path)
                    except Exception as exc:
                        self.category_model_available = False
                        self.load_errors.append(f"category 모델 로딩 실패: {exc}")

                if self.urgency_model_available:
                    try:
                        self.urgency_tokenizer = AutoTokenizer.from_pretrained(str(self.urgency_model_path))
                        self.urgency_model = AutoModelForSequenceClassification.from_pretrained(
                            str(self.urgency_model_path)
                        )
                        self.urgency_model.to(self.device)
                        self.urgency_model.eval()
                        self.urgency_id_to_label = self._load_id_to_label(self.urgency_model_path)
                    except Exception as exc:
                        self.urgency_model_available = False
                        self.load_errors.append(f"urgency 모델 로딩 실패: {exc}")
            except Exception as exc:
                self.category_model_available = False
                self.urgency_model_available = False
                self.load_errors.append(f"KoBERT 의존성 로딩 실패: {exc}")

            self.model_available = self.category_model_available or self.urgency_model_available

    def _resolve_task_path(self, task_name: str) -> Path:
        return task_model_path(self.model_path, task_name)

    def _load_id_to_label(self, model_path: Path) -> dict[int, str]:
        label_map_path = model_path / "label_map.json"
        if not label_map_path.exists():
            if model_path.name == "urgency":
                return ID_TO_URGENCY
            return ID_TO_LABEL
        label_map = json.loads(label_map_path.read_text(encoding="utf-8"))
        return {int(value): key for key, value in label_map.items()}

    def predict(self, text: str) -> dict:
        fallback = self.fallback.predict(text)
        if not self.model_available:
            result = fallback.to_dict()
            result["load_errors"] = self.load_errors
            return result

        if self.category_model_available:
            category, confidence, top_categories = self._predict_task(
                text,
                self.category_tokenizer,
                self.category_model,
                self.category_id_to_label,
            )
        else:
            category = fallback.category
            confidence = fallback.confidence
            top_categories = fallback.top_categories

        if self.urgency_model_available:
            urgency, urgency_confidence, _ = self._predict_task(
                text,
                self.urgency_tokenizer,
                self.urgency_model,
                self.urgency_id_to_label,
            )
        else:
            urgency = fallback.urgency
            urgency_confidence = fallback.urgency_confidence

        return PredictionResult(
            category=category,
            confidence=round(confidence, 4),
            urgency=urgency,
            urgency_confidence=round(urgency_confidence, 4),
            recommended_department=department_for_category(category),
            priority_level=priority_for_urgency(urgency),
            model_available=self.model_available,
            category_model_available=self.category_model_available,
            urgency_model_available=self.urgency_model_available,
            top_categories=top_categories,
            load_errors=self.load_errors,
        ).to_dict()

    def _predict_task(self, text: str, tokenizer, model, id_to_label: dict[int, str]):
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=self.max_length,
        )
        inputs = {key: value.to(self.device) for key, value in inputs.items()}

        with self.torch.no_grad():
            outputs = model(**inputs)
            probabilities = self.torch.softmax(outputs.logits, dim=1)[0]

        label_id = int(self.torch.argmax(probabilities).item())
        confidence = float(probabilities[label_id].item())
        top_values, top_indices = self.torch.topk(probabilities, k=min(3, len(id_to_label)))
        top_labels = [
            {
                "category": id_to_label[int(index.item())],
                "confidence": round(float(value.item()), 4),
            }
            for value, index in zip(top_values, top_indices)
        ]

        return id_to_label[label_id], confidence, top_labels
