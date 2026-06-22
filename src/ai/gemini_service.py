from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

try:
    import google.generativeai as genai
except ImportError:
    genai = None


REFINE_PROMPT = """
너는 학교 민원 문장을 중립적이고 사실 중심적인 표현으로 정제하는 전문가다.

목표:
학부모의 요구사항은 유지하되, 감정적 표현을 완화하고 학교 담당자가 처리하기 쉬운 문장으로 바꾼다.

원칙:
- 중립성 유지
- 교권 보호
- 학부모 표현권 보장
- 사실 중심 표현
- 요구사항 유지
- 비난, 단정, 위협 표현 완화
- 원문에 없는 사실 추가 금지

출력:
정제된 민원 문장만 출력한다.

원문:
{complaint_text}
""".strip()


STRUCTURE_PROMPT = """
너는 학교 민원을 행정 처리용 JSON으로 구조화하는 전문가다.

아래 민원을 분석하여 반드시 JSON만 출력하라.

출력 스키마:
{{
  "summary": "",
  "request": "",
  "urgency": "낮음|보통|높음",
  "stakeholders": [],
  "incident_date": "",
  "recommended_department": ""
}}

규칙:
- JSON 이외의 설명은 출력하지 않는다.
- 알 수 없는 날짜는 빈 문자열로 둔다.
- stakeholders에는 학부모, 학생, 담임교사, 행정실, 급식실 등 관련 주체를 넣는다.
- recommended_department는 교무부, 생활안전부, 행정실, 급식실, 시설관리 중 가장 적절한 곳을 선택한다.
- 원문에 없는 사실은 추가하지 않는다.

민원:
{complaint_text}

KoBERT 분류 결과:
{category}
""".strip()


COMBINED_PROMPT = """
너는 학교 민원 문장을 정제하고 행정 처리용 JSON으로 구조화하는 전문가다.

목표:
학부모의 요구사항은 유지하되, 감정적 표현을 완화하고 학교 담당자가 처리하기 쉬운 문장으로 바꾼다.

원칙:
- 중립성 유지
- 교권 보호
- 학부모 표현권 보장
- 사실 중심 표현
- 요구사항 유지
- 비난, 단정, 위협 표현 완화
- 원문에 없는 사실 추가 금지

반드시 JSON만 출력하라.

출력 스키마:
{{
  "refined": "",
  "structured": {{
    "summary": "",
    "request": "",
    "urgency": "낮음|보통|높음",
    "stakeholders": [],
    "incident_date": "",
    "recommended_department": ""
  }}
}}

규칙:
- JSON 이외의 설명은 출력하지 않는다.
- 알 수 없는 날짜는 빈 문자열로 둔다.
- stakeholders에는 학부모, 학생, 담임교사, 행정실, 급식실 등 관련 주체를 넣는다.
- recommended_department는 교무부, 생활안전부, 행정실, 급식실, 시설관리 중 가장 적절한 곳을 선택한다.
- 원문에 없는 사실은 추가하지 않는다.

민원 원문:
{complaint_text}

KoBERT 분류 결과:
{category}
""".strip()


DEPARTMENT_BY_CATEGORY = {
    "수업/학습 문제": "교무부",
    "교사 태도/행동": "교무부",
    "시설/환경": "시설관리",
    "급식": "급식실",
    "생활지도/안전": "생활안전부",
    "기타": "행정실",
}

VALID_URGENCY = {"낮음", "보통", "높음"}
VALID_DEPARTMENT = {"교무부", "생활안전부", "행정실", "급식실", "시설관리"}


@dataclass
class GeminiResult:
    refined_text: str
    structured_json: dict
    model_available: bool


class GeminiService:
    def __init__(self, api_key: str | None = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.model_available = bool(self.api_key) and genai is not None

        if self.model_available:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None

    def refine_text(self, complaint_text: str) -> str:
        if not self.model_available:
            return self._fallback_refine(complaint_text)

        try:
            response = self.model.generate_content(
                REFINE_PROMPT.format(complaint_text=complaint_text)
            )
            return response.text.strip()
        except Exception:
            return self._fallback_refine(complaint_text)

    def structure_complaint(self, complaint_text: str, category: str) -> dict:
        if not self.model_available:
            return self._fallback_structure(complaint_text, category)

        try:
            response = self.model.generate_content(
                STRUCTURE_PROMPT.format(complaint_text=complaint_text, category=category)
            )
            return self._normalize_structure(
                self._parse_json(response.text),
                complaint_text,
                category,
            )
        except Exception:
            return self._fallback_structure(complaint_text, category)

    def process(self, complaint_text: str, category: str) -> GeminiResult:
        if not self.model_available:
            refined = self._fallback_refine(complaint_text)
            structured = self._fallback_structure(refined, category)
            return GeminiResult(
                refined_text=refined,
                structured_json=structured,
                model_available=False,
            )

        try:
            response = self.model.generate_content(
                COMBINED_PROMPT.format(complaint_text=complaint_text, category=category)
            )
            parsed = self._parse_json(response.text)
            refined = parsed.get("refined") or self._fallback_refine(complaint_text)
            structured = self._normalize_structure(
                parsed.get("structured") or {},
                refined,
                category,
            )
            model_available = True
        except Exception:
            refined = self._fallback_refine(complaint_text)
            structured = self._fallback_structure(refined, category)
            model_available = False

        return GeminiResult(
            refined_text=refined,
            structured_json=structured,
            model_available=model_available,
        )

    def _parse_json(self, raw_text: str) -> dict:
        cleaned = raw_text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {
                "summary": cleaned[:120],
                "request": "",
                "urgency": "보통",
                "stakeholders": [],
                "incident_date": "",
                "recommended_department": "교무부",
            }

    def _normalize_structure(self, structured: dict, complaint_text: str, category: str) -> dict:
        fallback_department = DEPARTMENT_BY_CATEGORY.get(category, "행정실")

        normalized = {
            "summary": structured.get("summary") or complaint_text[:80],
            "request": structured.get("request") or "관련 내용 확인 및 필요한 조치를 요청합니다.",
            "urgency": structured.get("urgency") or "보통",
            "stakeholders": structured.get("stakeholders") or ["학부모", "학생", "학교 담당자"],
            "incident_date": structured.get("incident_date") or "",
            "recommended_department": structured.get("recommended_department") or fallback_department,
        }

        if normalized["urgency"] not in VALID_URGENCY:
            normalized["urgency"] = "보통"
        if normalized["recommended_department"] not in VALID_DEPARTMENT:
            normalized["recommended_department"] = fallback_department
        if not isinstance(normalized["stakeholders"], list):
            normalized["stakeholders"] = [str(normalized["stakeholders"])]

        return normalized

    def _fallback_refine(self, complaint_text: str) -> str:
        return (
            "입력하신 사안에 대해 사실관계 확인과 검토를 요청드립니다. "
            f"세부 내용: {complaint_text}"
        )

    def _fallback_structure(self, complaint_text: str, category: str) -> dict:
        return {
            "summary": complaint_text[:80],
            "request": "관련 내용 확인 및 필요한 조치를 요청합니다.",
            "urgency": "보통",
            "stakeholders": ["학부모", "학생", "학교 담당자"],
            "incident_date": "",
            "recommended_department": DEPARTMENT_BY_CATEGORY.get(category, "행정실"),
        }
