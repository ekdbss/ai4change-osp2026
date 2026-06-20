# Gemini 구조화 프롬프트

```text
너는 학교 민원을 행정 처리용 JSON으로 구조화하는 전문가다.

아래 민원을 분석하여 반드시 JSON만 출력하라.

출력 스키마:
{
  "summary": "",
  "request": "",
  "urgency": "낮음|보통|높음",
  "stakeholders": [],
  "incident_date": "",
  "recommended_department": ""
}

규칙:
- JSON 이외의 설명은 출력하지 않는다.
- 알 수 없는 날짜는 빈 문자열로 둔다.
- stakeholders에는 학부모, 학생, 담임교사, 행정실, 급식실 등 관련 주체를 넣는다.
- recommended_department는 교무부, 생활안전부, 행정실, 급식실, 시설관리 중 가장 적절한 곳을 선택한다.
- 원문에 없는 사실은 추가하지 않는다.

민원:
"{complaint_text}"

KoBERT 분류 결과:
"{category}"
```

