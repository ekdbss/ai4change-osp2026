from __future__ import annotations

from src.ai.gemini_service import GeminiService
from src.ai.kobert_predictor import KoBERTPredictor
from src.ai.pii_masker import mask_sensitive_info


def process_complaint(
    title: str,
    original_text: str,
    classifier: KoBERTPredictor,
    gemini_service: GeminiService,
) -> dict:
    masked_text = mask_sensitive_info(original_text)
    prediction = classifier.predict(masked_text)
    gemini_result = gemini_service.process(masked_text, prediction["category"])
    structured = gemini_result.structured_json

    return {
        "title": title,
        "original_text": original_text,
        "masked_text": masked_text,
        "refined_text": gemini_result.refined_text,
        "structured_json": structured,
        "category": prediction["category"],
        "confidence": prediction["confidence"],
        "status": "접수",
        "recommended_department": structured.get("recommended_department", ""),
        "kobert_model_available": prediction["model_available"],
        "gemini_model_available": gemini_result.model_available,
    }

