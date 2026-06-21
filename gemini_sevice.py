import google.generativeai as genai
import json
import os

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        else:
            print("[경고] GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

        self.system_instruction = """당신은 학교 민원 처리 시스템의 핵심 요약 AI입니다.
학부모가 작성한 민원 내용에서 감정적인 표현이나 비난은 배제하고, 관리자가 반드시 알아야 할 핵심 정보만 객관적으로 추출하여 JSON 형식으로 반환하세요.

[출력 JSON 스키마]
{
  "summary": "민원의 핵심 내용 요약 (1~2줄, 매우 객관적인 어조)",
  "request": "학부모의 구체적인 요구 사항",
  "urgency": "상황의 긴급도 (상/중/하 중 택1)",
  "stakeholders": ["관련된 사람들의 이름이나 직책 목록 (예: '민준', '담임교사')"],
  "incident_date": "사건 발생 일시 (내용 중 파악 불가 시 '알 수 없음')",
  "recommended_department": "추천 담당 부서 (예: 교무처, 행정실, 학생부 등)"
}"""

        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash", 
            system_instruction=self.system_instruction,
            generation_config={"response_mime_type": "application/json"}
        )

    def analyze_complaint(self, complaint_text: str) -> dict:
        """민원 텍스트를 받아 정해진 JSON 스키마의 딕셔너리로 반환합니다."""
        try:
            response = self.model.generate_content(complaint_text)
            return json.loads(response.text)
        except Exception as e:
            return {"error": f"분석 실패: {str(e)}"}

if __name__ == "__main__":
    service = GeminiService()
    test_input = "민준이 엄만데요, 민준이가 당근을 학교에서 먹었다네요. 선생이란 게 어떻게 그럴 수 있어요? 당장 전화주세요."
    
    print(json.dumps(service.analyze_complaint(test_input), indent=4, ensure_ascii=False))