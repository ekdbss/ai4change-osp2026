# 학교 민원 AI 정제 및 자동 분류 플랫폼

Team 숙크크(SCC) Open Source Programming Team Project 2026-1

AI 기반 학부모 민원 관리 플랫폼 | Open-Source Project 2026

## 프로젝트 개요

SCC는 학부모 민원을 디지털로 접수하고, 팀이 직접 Fine-Tuning한 KoBERT 모델로 민원 카테고리와 처리 긴급도를 자동 판단하는 Streamlit 기반 웹 플랫폼입니다.

Gemini API는 보조 AI로 사용하여 감정적 표현을 중립적이고 사실 중심적인 민원 문장으로 정제하고, 행정 처리에 필요한 정보를 구조화합니다. 핵심 평가 포인트는 단순 생성형 AI API 호출이 아니라, 직접 구축한 학습 데이터와 직접 학습한 KoBERT 모델을 서비스의 핵심 판단 흐름에 적용했다는 점입니다.

## 주요 기능

- 학부모 민원 작성 및 첨부파일 등록
- 학부모 STT 음성 입력 및 TTS 읽어주기 접근성 기능
- KoBERT Fine-Tuning 모델 기반 민원 카테고리 자동 분류
- KoBERT 기반 처리 긴급도 자동 판단
- Gemini 기반 감정 정제 및 행정 처리용 JSON 구조화
- Aiven MySQL 기반 민원 저장
- 관리자 민원 목록 조회, 상태 변경, 처리 의견 저장
- 카테고리별/상태별/월별 통계 시각화
- 모델 학습 데이터와 평가 결과 확인

## 처리 파이프라인

```text
학부모 민원 입력
  -> 개인정보/민감 표현 마스킹
  -> KoBERT 카테고리/긴급도 판단
  -> Gemini 감정 정제 및 JSON 구조화
  -> MySQL 저장
  -> 관리자 대시보드 처리
  -> 학부모 처리 현황 조회
```

## 기술 스택

- Frontend: Streamlit
- Backend: Python
- Database: MySQL, Aiven for MySQL
- AI Model: KoBERT, PyTorch, HuggingFace Transformers
- Generative AI: Gemini 2.5 Flash
- Deployment: Streamlit Cloud

## 데모 운영 범위

본 프로젝트는 수업 프로젝트 시연을 목적으로 개발한 MVP입니다. 현재 서비스 화면에서는 모든 학교를 제공하지 않고, 서울특별시교육청 소속 일부 데모 학교(`새봄초등학교`, `증산초등학교`)만 선택지로 제공합니다.

실제 서비스화 단계에서는 교육청/학교 목록을 코드 상수로 관리하지 않고, 교육청 학교 목록 데이터베이스 또는 공공데이터 API와 연동하여 학교 선택지를 자동으로 동기화할 예정입니다.

## 실행 방법

```bash
pip install -r requirements.txt
cp .env.example .env
python scripts/init_database.py
streamlit run app.py
```

MySQL을 사용할 경우 `.env`에 DB 접속 정보를 입력한 뒤 `scripts/init_database.py`를 실행합니다. Streamlit Cloud에서는 `.env` 대신 App settings > Secrets에 값을 입력합니다.

## Streamlit Cloud 배포

배포 서버는 로컬 PC의 `.env`, MySQL, 모델 zip 파일을 자동으로 가져가지 않습니다. Cloud 배포 시에는 Streamlit Secrets에 Gemini/MySQL 값을 넣고, KoBERT 모델 zip은 GitHub Release 다운로드 URL로 연결합니다.

자세한 절차는 `docs/streamlit-cloud-deployment.md`를 참고합니다.

## 모델 학습 순서

```bash
python scripts/prepare_training_data.py --input data/raw/generated_complaints_final_1800.csv
python model/train_kobert.py --epochs 6 --batch-size 16 --max-length 128
python model/evaluate.py
```

학습된 모델은 `model/saved_model`에 저장됩니다. 배포 환경에서는 `KOBERT_MODEL_ZIP_URL`에 설정된 zip 파일을 앱이 자동으로 다운로드하여 `model/saved_model`에 설치합니다.

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
    1_submit_complaint.py
    2_admin_dashboard.py
    3_statistics.py
    4_model_report.py
  src/
    ai/
      gemini_service.py
      kobert_predictor.py
      label_map.py
      model_artifacts.py
      pii_masker.py
    db/
      connection.py
      complaint_repository.py
    services/
      auth_service.py
      complaint_service.py
      session_store.py
    utils/
      validators.py
  model/
    dataset.py
    train_kobert.py
    evaluate.py
  data/
    raw/
    processed/
  docs/
  prompts/
  reports/
  scripts/
  sql/
```

## 배포용 주요 환경변수

```toml
GEMINI_API_KEY = "your-gemini-api-key"

KOBERT_MODEL_ZIP_URL = "https://github.com/ekdbss/scc-osp2026/releases/download/v0-kobert-1800/kobert_v1_1800.zip"
KOBERT_MODEL_ZIP_SHA256 = "a8434b4b3e625282ec40dedf73dbad046170bcac7011f7ccedc798a3f15e1630"

DB_HOST = "scc-osp2026-mysql-scc-osp2026.h.aivencloud.com"
DB_PORT = "23464"
DB_USER = "avnadmin"
DB_PASSWORD = "your-aiven-password"
DB_NAME = "defaultdb"
DB_SSL_MODE = "REQUIRED"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin1234"
```
