from __future__ import annotations

from src.ai.gemini_service import GeminiService
from src.ai.kobert_predictor import KoBERTPredictor
from src.ai.pii_masker import mask_sensitive_info


def process_complaint(
    title: str,
    original_text: str,
    classifier: KoBERTPredictor,
    gemini_service: GeminiService,
    complaint_meta: dict | None = None,
) -> dict:
    complaint_meta = complaint_meta or {}
    masked_text = mask_sensitive_info(original_text)
    prediction = classifier.predict(masked_text)
    gemini_result = gemini_service.process(masked_text, prediction["category"])
    structured = gemini_result.structured_json
    ai_category = prediction["category"]

    return {
        **complaint_meta,
        "title": title,
        "original_text": original_text,
        "masked_text": masked_text,
        "refined_text": gemini_result.refined_text,
        "structured_json": structured,
        "ai_category": ai_category,
        "final_category": ai_category,
        "ai_confidence": prediction["confidence"],
        "priority_level": _default_priority(ai_category, structured.get("urgency")),
        "status": "접수",
        "recommended_department": structured.get("recommended_department", ""),
        "parent_visible_comment": "",
        "kobert_model_available": prediction["model_available"],
        "gemini_model_available": gemini_result.model_available,
        # Backward-compatible aliases for demo/session code that may still read old keys.
        "category": ai_category,
        "confidence": prediction["confidence"],
    }


def _default_priority(category: str, urgency: str | None = None) -> int:
    if urgency == "높음":
        return 1
    if urgency == "낮음":
        return 4

    category_priority = {
        "교사 태도/행동": 1,
        "생활지도/안전": 1,
        "수업/학습 문제": 2,
        "시설/환경": 3,
        "급식": 3,
        "기타": 4,
    }
    return category_priority.get(category, 3)
