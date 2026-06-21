from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.ai.label_map import ID_TO_LABEL


@dataclass
class PredictionResult:
    category: str
    confidence: float
    model_available: bool

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "confidence": self.confidence,
            "model_available": self.model_available,
        }


class KeywordFallbackClassifier:
    """Development fallback used only until the fine-tuned KoBERT model exists."""

    RULES = {
        "급식": ["급식", "반찬", "식단", "알레르기", "우유", "음식", "위생", "배식"],
        "시설/환경": ["교실", "화장실", "에어컨", "난방", "시설", "환경", "소음", "공사"],
        "생활지도/안전": ["폭력", "따돌림", "안전", "등교", "하교", "운동장", "사고", "생활지도"],
        "교사 태도/행동": ["선생님", "교사", "담임", "말투", "무시", "차별", "상담", "태도"],
        "수업/학습 문제": ["수업", "숙제", "과제", "시험", "평가", "진도", "설명", "학습"],
    }

    def predict(self, text: str) -> PredictionResult:
        scores = {label: 0 for label in ID_TO_LABEL.values()}
        for label, words in self.RULES.items():
            scores[label] = sum(1 for word in words if word in text)

        best_label = max(scores, key=scores.get)
        if scores[best_label] == 0:
            best_label = "기타"

        return PredictionResult(
            category=best_label,
            confidence=0.50,
            model_available=False,
        )


class KoBERTPredictor:
    def __init__(self, model_path: str, max_length: int = 128):
        self.model_path = Path(model_path)
        self.max_length = max_length
        self.fallback = KeywordFallbackClassifier()
        self.model_available = self._has_saved_model()
        self.torch = None
        self.device = None

        if self.model_available:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            self.torch = torch
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
            self.model = AutoModelForSequenceClassification.from_pretrained(str(self.model_path))
            self.model.to(self.device)
            self.model.eval()
        else:
            self.tokenizer = None
            self.model = None

    def _has_saved_model(self) -> bool:
        return (self.model_path / "config.json").exists()

    def predict(self, text: str) -> dict:
        if not self.model_available:
            return self.fallback.predict(text).to_dict()

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=self.max_length,
        )
        inputs = {key: value.to(self.device) for key, value in inputs.items()}

        with self.torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = self.torch.softmax(outputs.logits, dim=1)[0]

        label_id = int(self.torch.argmax(probabilities).item())
        confidence = float(probabilities[label_id].item())

        return PredictionResult(
            category=ID_TO_LABEL[label_id],
            confidence=round(confidence, 4),
            model_available=True,
        ).to_dict()
