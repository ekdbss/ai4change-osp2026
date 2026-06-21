from __future__ import annotations

from src.ai.gemini_service import GeminiService
from src.ai.kobert_predictor import KoBERTPredictor
from src.ai.pii_masker import mask_sensitive_info
from src.ai.label_map import priority_for_urgency


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
    ai_urgency = prediction.get("urgency", structured.get("urgency", "보통"))
    recommended_department = prediction.get("recommended_department") or structured.get(
        "recommended_department",
        "",
    )
    structured["urgency"] = ai_urgency
    structured["recommended_department"] = recommended_department

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
        "ai_urgency": ai_urgency,
        "final_urgency": ai_urgency,
        "urgency_confidence": prediction.get("urgency_confidence"),
        "priority_level": prediction.get("priority_level") or priority_for_urgency(ai_urgency),
        "status": "접수",
        "recommended_department": recommended_department,
        "parent_visible_comment": "",
        "kobert_model_available": prediction["model_available"],
        "category_model_available": prediction.get("category_model_available", False),
        "urgency_model_available": prediction.get("urgency_model_available", False),
        "gemini_model_available": gemini_result.model_available,
        "top_categories": prediction.get("top_categories", []),
        # Backward-compatible aliases for demo/session code that may still read old keys.
        "category": ai_category,
        "confidence": prediction["confidence"],
    }
