# 학교 민원 AI 정제 및 자동 분류 플랫폼

Team 숙크크(SCC) Open Source Programming Team Project 2026-1

## 프로젝트 목표

이 프로젝트는 학부모 민원을 디지털로 접수하고, 팀이 직접 Fine-Tuning한 KoBERT 모델로 민원 카테고리를 자동 분류한 뒤, Gemini를 보조 AI로 사용해 감정 표현을 정제하고 행정 처리용 JSON으로 구조화하는 서비스입니다.

핵심 평가 포인트는 단순 생성형 AI API 호출이 아니라 직접 개발한 KoBERT 분류 모델을 서비스 흐름에 적용하는 것입니다.

## MVP 기능

- 학부모 민원 작성
- KoBERT 기반 자동 분류
- Gemini 기반 감정 정제
- Gemini 기반 JSON 구조화
- MySQL 저장
- 관리자 민원 목록 조회
- 상태 변경
- 카테고리별, 상태별 통계
- 모델 평가 결과 확인

## 기술 스택

- Frontend: Streamlit
- Backend: Python
- Database: MySQL
- AI Model: KoBERT, PyTorch, HuggingFace Transformers
- Generative AI: Gemini 2.5 Flash
- Deployment: Streamlit Cloud

## 실행 방법

```bash
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

MySQL을 사용할 경우 `sql/schema.sql`을 먼저 실행하고 `.env`에 DB 접속 정보를 입력합니다.

## 모델 학습 순서

```bash
python scripts/generate_synthetic_data.py
python model/train_kobert.py
python model/evaluate.py
```

학습된 모델은 `model/saved_model`에 저장되며, Streamlit 앱의 KoBERT 추론 모듈이 이 경로를 자동으로 사용합니다.

## 민원 분류 카테고리

- 수업/학습 문제
- 교사 태도/행동
- 시설/환경
- 급식
- 생활지도/안전
- 기타

## 프로젝트 구조

```text
scc-osp2026/
  app.py
  pages/
  src/
    ai/
    db/
    services/
    utils/
  model/
  data/
  sql/
  reports/
  prompts/
  scripts/
```

