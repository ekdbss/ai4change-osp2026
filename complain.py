import google.generativeai as genai
import json

GOOGLE_API_KEY = "여기에_복사한_API_KEY_넣기"
genai.configure(api_key=GOOGLE_API_KEY)


system_instruction = """
당신은 학교 민원 처리 시스템의 핵심 요약 AI입니다.
학부모가 작성한 민원 내용에서 감정적인 표현이나 비난은 모두 배제하고, 관리자가 반드시 알아야 할 핵심 정보만 객관적으로 추출하여 반드시 JSON 형식으로만 반환하세요. 다른 부가적인 설명은 절대 하지 마세요.

[출력 JSON 구조]
{
  "issue_summary": "민원의 핵심 내용 요약 (1~2줄, 매우 객관적인 어조)",
  "student_info": "언급된 학생의 정보 (학년, 반, 이름 등. 언급이 없다면 '알 수 없음')",
  "demands": "학부모의 구체적인 요구 사항",
  "urgency": "상황의 긴급도 (상/중/하)",
  "emotion_filtered": "필터링된 감정적 키워드 (예: 분노, 우려, 당혹)"
}
"""

model = genai.GenerativeModel(
    model_name="gemini-3-flash-preview", 
    system_instruction=system_instruction,
    generation_config={"response_mime_type": "application/json"}
)

def process_complaint(complaint_text):
    print("AI가 민원을 분석 중입니다...\n")
    try:
        response = model.generate_content(complaint_text)
        result_data = json.loads(response.text)
        return result_data
    except Exception as e:
        return {"error": f"분석 실패: {str(e)}"}


if __name__ == "__main__":
    
    test_input = "민준이 엄만데요, 민준이가 당근을 학교에서 먹었다네요. 선생이란 게 어떻게 그럴 수 있어요? 당장 전화주세요."
    
    
    final_result = process_complaint(test_input)
    
    print("=== 백엔드로 넘어갈 JSON 데이터 ===")
    print(json.dumps(final_result, indent=4, ensure_ascii=False))