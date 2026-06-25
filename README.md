# 학교 민원 AI 정제 및 자동 분류 플랫폼

#### Team 숙크크(SCC) | 숙명여자대학교 인공지능공학부 | Open Source Programming 2026-1

AI 기반 학부모 민원 관리 플랫폼 | Open-Source Project 2026

---

## Quick Start

아래 순서대로 실행하면 동일한 개발 환경에서 서비스를 재현할 수 있습니다.

```bash
conda create --name scc python=3.11.7
conda activate scc
pip install -r requirements.txt
cp .env.example .env
python scripts/init_database.py
streamlit run app.py
```

- 학습 데이터 경로: `data/raw/generated_complaints_final_1800.csv`
- KoBERT 학습 명령: `python model/train_kobert.py --epochs 6 --batch-size 16 --max-length 128`
- 모델 평가 명령: `python model/evaluate.py`
- 배포 설정 예시는 `.streamlit/secrets.example.toml`과 `docs/streamlit-cloud-deployment.md`를 참고합니다.

---

## Live Demo

- Service URL: [학교민원 분류 AI](https://scc-osp2026-rxkfedeswl75xfzqjsg8x2.streamlit.app/)

> Streamlit Cloud 무료 배포 환경 특성상 최초 접속 시 앱 로딩에 시간이 걸릴 수 있습니다.

---

## 프로젝트 개요

**SCC**는 학부모 민원을 디지털로 접수하고, 팀이 직접 Fine-Tuning한 KoBERT 모델로 민원 카테고리와 처리 긴급도를 자동 판단하는 Streamlit 기반 웹 플랫폼입니다.

Gemini API는 보조 AI로 활용하여 감정적 표현을 중립적이고 사실 중심적인 민원 문장으로 정제하고, 행정 처리에 필요한 정보를 구조화합니다. 핵심은 단순 생성형 AI API 호출이 아니라, **직접 구축한 학습 데이터와 직접 학습한 KoBERT 모델을 서비스의 핵심 판단 흐름에 적용**했다는 점입니다.

### 주요 기능

- 학부모 민원 작성 및 첨부파일 등록
- STT 음성 입력 및 TTS 읽어주기 접근성 기능
- KoBERT Fine-Tuning 모델 기반 민원 카테고리 자동 분류
- KoBERT 기반 처리 긴급도 자동 판단
- Gemini 기반 감정 정제 및 행정 처리용 JSON 구조화
- Aiven MySQL 기반 민원 저장
- 관리자 민원 목록 조회, 상태 변경, 처리 의견 저장
- 카테고리별/상태별/월별 통계 시각화
- 모델 학습 데이터 및 평가 결과 확인

### 민원 분류 카테고리

| 카테고리 | 설명 |
|---------|------|
| 수업/학습 문제 | 수업 방식, 학습 자료, 교육과정 관련 |
| 교사 태도/행동 | 교사의 언행, 학생 응대 방식 관련 |
| 시설/환경 | 교실, 화장실, 운동장 등 학교 시설 관련 |
| 급식 | 급식 품질, 위생, 식단 관련 |
| 생활지도/안전 | 학교폭력, 안전사고, 생활지도 관련 |
| 기타 | 위 카테고리에 해당하지 않는 민원 |

---

## 처리 파이프라인

```text
학부모 민원 입력
      │
      ▼
개인정보/민감 표현 마스킹 (pii_masker.py)
      │
      ▼
KoBERT 카테고리 + 긴급도 판단 (kobert_predictor.py)
      │
      ▼
Gemini 감정 정제 + JSON 구조화 (gemini_service.py)
      │
      ▼
MySQL 저장 (complaint_repository.py)
      │
      ▼
관리자 대시보드 처리 → 학부모 처리 현황 조회
```

---

## 기술 스택

| 분류 | 기술 |
|------|------|
| Frontend | Streamlit |
| Backend | Python 3.11.7 |
| Database | MySQL, Aiven for MySQL |
| AI Model | KoBERT (`skt/kobert-base-v1`), PyTorch, HuggingFace Transformers |
| Generative AI | Gemini 2.5 Flash |
| Deployment | Streamlit Cloud |

---

## 데모 운영 범위

본 프로젝트는 수업 프로젝트 시연을 목적으로 개발한 MVP입니다. 현재 서비스 화면에서는 서울특별시교육청 소속 일부 데모 학교(`새봄초등학교`, `증산초등학교`)만 선택지로 제공합니다.

실제 서비스화 단계에서는 교육청 학교 목록 데이터베이스 또는 공공데이터 API와 연동하여 학교 선택지를 자동으로 동기화할 예정입니다.

---

## 프로젝트 구조

```
.
├── LICENSE
├── README.md
├── .env.example                    # 로컬 실행용 환경변수 예시
├── app.py                          # Streamlit 엔트리포인트
├── classifier.py                   # 분류 파이프라인 통합
├── db.py                           # DB 연결 설정 (SQLAlchemy)
├── requirements.txt
│
├── data/
│   ├── raw/                        # 원본 합성 데이터
│   │   ├── generated_complaints.csv
│   │   ├── generated_complaints_backup.csv
│   │   ├── generated_complaints_final_1800.csv  # 최종 학습용 (1800건)
│   │   ├── generated_complaints_hq_1800.csv
│   │   ├── generated_complaints_merged_1500.csv
│   │   ├── generated_complaints_multitask.csv
│   │   ├── generated_complaints_reviewed.csv
│   │   ├── additional_complaints_300.csv
│   │   └── additional_complaints_round2.csv
│   ├── processed/                  # 전처리 완료 데이터 (train/valid/test split)
│   │   ├── train.csv
│   │   ├── valid.csv
│   │   └── test.csv
│   └── review/                     # 라벨 검수 샘플
│       └── label_review_sample_300.csv
│
├── model/
│   ├── train_kobert.py             # KoBERT 파인튜닝 학습 스크립트
│   ├── dataset.py                  # 커스텀 Dataset 클래스
│   ├── evaluate.py                 # 모델 평가 스크립트
│   └── saved_model/                # 실행 시 설치/생성되는 파인튜닝 모델 경로
│       ├── category/               # 카테고리 분류 모델
│       └── urgency/                # 긴급도 분류 모델
│
├── pages/                          # Streamlit 멀티페이지
│   ├── 1_submit_complaint.py       # 민원 접수 페이지 (학부모)
│   ├── 2_admin_dashboard.py        # 관리자 대시보드
│   ├── 3_statistics.py             # 통계 시각화
│   └── 4_model_report.py           # 학습 결과 확인용 보조 페이지
│
├── prompts/                        # Gemini 프롬프트 템플릿
│   ├── data_generation_prompt.md
│   ├── gemini_refine_prompt.md
│   ├── gemini_structure_prompt.md
│   └── high_quality_data_generation_prompt.md
│
├── reports/                        # 실험 결과 리포트 저장 경로
│
├── scripts/                        # 데이터 생성 및 DB 관리 유틸리티
│   ├── generate_synthetic_data.py
│   ├── generate_high_quality_dataset.py
│   ├── expand_training_data_offline.py
│   ├── prepare_training_data.py        # train/valid/test split
│   ├── make_label_review_sample.py
│   ├── apply_label_review.py
│   ├── fill_label_review_defaults.py
│   ├── init_database.py                # DB 초기화
│   ├── reset_database.py
│   ├── seed_demo_complaints.py
│   ├── migrate_add_login_profile_fields.py
│   ├── migrate_add_urgency_fields.py
│   └── install_colab_model.py
│
├── sql/
│   ├── schema.sql                  # DB 테이블 생성 스크립트
│   ├── seed_admin.sql              # 초기 관리자 계정 시드 데이터
│   └── migrations/
│       ├── 2026_06_22_add_login_profile_fields.sql
│       └── 2026_06_22_add_urgency_fields.sql
│
├── docs/
│   ├── labeling_guideline.md
│   ├── streamlit-cloud-deployment.md
│   └── v0-test-result.md
│
└── src/
    ├── config.py
    ├── ai/
    │   ├── gemini_service.py       # Gemini API 호출 (정제 + 구조화)
    │   ├── kobert_predictor.py     # KoBERT 추론 모듈
    │   ├── pii_masker.py           # 개인정보 마스킹
    │   ├── label_map.py            # 카테고리 라벨 매핑
    │   └── model_artifacts.py      # 모델 파일 로드 유틸
    ├── db/
    │   ├── complaint_repository.py # 민원 CRUD
    │   └── connection.py           # DB 연결 (pymysql)
    ├── services/
    │   ├── auth_service.py         # 로그인/인증
    │   ├── complaint_service.py    # 비즈니스 로직
    │   └── session_store.py        # 세션 상태 관리
    └── utils/
        └── validators.py           # 입력값 검증
```

---

## Getting Started

### 1. 환경 설정

Python **3.11.7** 환경을 권장합니다.

```bash
# 가상환경 생성 (conda 사용 시)
conda create --name scc python=3.11.7
conda activate scc

# 또는 venv 사용 시 (Mac/ARM 기준)
python3 -m venv venv-arm
source venv-arm/bin/activate
```

### 2. 의존성 패키지 설치

```bash
pip install -r requirements.txt
```

주요 패키지 버전:

| 분류 | 패키지 | 버전 |
|------|--------|------|
| Frontend | `streamlit` | `>=1.58.0` |
| Data & ML | `pandas` | `>=2.0.0` |
| | `numpy` | `>=1.24.0` |
| | `scikit-learn` | `>=1.4.0` |
| | `matplotlib` | `>=3.8.0` |
| NLP & DL | `torch` | `>=2.1.0` |
| | `transformers` | `>=4.41.0` |
| | `accelerate` | `>=0.30.0` |
| DB & GenAI | `pymysql` | `>=1.1.0` |
| | `python-dotenv` | `>=1.0.1` |
| | `google-generativeai` | `>=0.7.0` |

### 3. 환경변수 설정

`.env.example`을 복사하여 `.env`를 생성하고, 아래 항목을 채워넣으세요.

```bash
cp .env.example .env
```

```env
GEMINI_API_KEY=your-gemini-api-key

DB_HOST=your-db-host
DB_PORT=3306
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_NAME=scc_osp2026
DB_SSL_MODE=REQUIRED

ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-admin-password

BASE_MODEL_NAME=skt/kobert-base-v1
KOBERT_MODEL_PATH=model/saved_model
KOBERT_MODEL_ZIP_URL=https://github.com/ekdbss/scc-osp2026/releases/download/v0-kobert-1800/kobert_v1_1800.zip
KOBERT_MODEL_ZIP_SHA256=a8434b4b3e625282ec40dedf73dbad046170bcac7011f7ccedc798a3f15e1630
```

> Streamlit Cloud에서는 `.env` 대신 **App settings > Secrets**에 위 값을 입력합니다. 자세한 절차는 `docs/streamlit-cloud-deployment.md`를 참고하세요.

### 4. 데이터베이스 초기화

```bash
python scripts/init_database.py
```

> 로컬 테스트 시 `.env`에 `DATABASE_URL=sqlite:///complaints_test.db`를 추가하면 SQLite로 동작합니다. (단, `db.py` 경유 기능만 해당. `connection.py`는 MySQL 전용)

### 5. 모델 파일 준비

파인튜닝된 KoBERT 모델 파일을 `model/saved_model/` 경로에 위치시킵니다.

```
model/saved_model/
├── category/
│   ├── config.json
│   ├── label_map.json
│   ├── model.safetensors
│   ├── tokenizer.json
│   └── tokenizer_config.json
└── urgency/
    ├── config.json
    ├── label_map.json
    ├── model.safetensors
    ├── tokenizer.json
    └── tokenizer_config.json
```

> 배포 환경에서는 `KOBERT_MODEL_ZIP_URL`에 설정된 zip 파일을 앱이 자동으로 다운로드하여 `model/saved_model`에 설치합니다.

### 6. 앱 실행

```bash
streamlit run app.py
```

---

## 학습 데이터

최종 학습 데이터셋은 `data/raw/generated_complaints_final_1800.csv`입니다. 총 1,800건으로 구성되어 있으며, 6개 민원 카테고리별 300건씩 균형 있게 포함되어 있습니다. 각 데이터는 민원 원문(`text`), 카테고리(`category`), 긴급도(`urgency`), 데이터 출처(`source`) 컬럼을 포함합니다.

긴급도는 `높음`, `보통`, `낮음`의 3단계로 구성했습니다. 실제 학생, 학부모, 교직원의 개인정보는 포함하지 않으며, 학교 민원 처리 시나리오에 맞춰 생성한 합성 데이터와 검수 데이터를 사용했습니다.

합성 데이터는 아래 스크립트로 생성할 수 있습니다.

```bash
python scripts/generate_synthetic_data.py
```

| 경로 | 설명 |
|------|------|
| `data/raw/generated_complaints_final_1800.csv` | 최종 학습용 데이터 (1800건) |
| `data/raw/generated_complaints_hq_1800.csv` | 고품질 증강 데이터 (1800건) |
| `data/raw/generated_complaints_merged_1500.csv` | 병합 데이터 (1500건) |
| `data/raw/additional_complaints_300.csv` | 추가 증강 데이터 (300건) |
| `data/raw/additional_complaints_round2.csv` | 2차 추가 증강 데이터 |
| `data/review/label_review_sample_300.csv` | 라벨 검수 샘플 (300건) |
| `data/processed/train.csv` | 학습 split |
| `data/processed/valid.csv` | 검증 split |
| `data/processed/test.csv` | 테스트 split |

---

## KoBERT 모델 학습

```bash
python scripts/prepare_training_data.py --input data/raw/generated_complaints_final_1800.csv
python model/train_kobert.py --epochs 6 --batch-size 16 --max-length 128
python model/evaluate.py
```

학습 완료 후 모델은 자동으로 `model/saved_model/`에 저장됩니다.

---

## DB 스키마

주요 테이블은 다음과 같습니다. 자세한 DDL은 `sql/schema.sql`을 참고하세요.

| 테이블 | 주요 컬럼 | 설명 |
|--------|-----------|------|
| `users` | `login_id`, `parent_name`, `school_name`, `student_grade`, `student_class`, `student_number`, `student_name` | 학부모 계정 및 학생 식별 정보 |
| `admins` | `username`, `password_hash`, `role`, `region_name`, `school_name` | 교사/관리자 계정 및 소속 학교 정보 |
| `category_priority_settings` | `category`, `priority_level`, `description` | 카테고리별 기본 처리 우선순위 설정 |
| `complaints` | `title`, `original_text`, `refined_text`, `ai_category`, `final_category`, `ai_urgency`, `final_urgency`, `status`, `parent_visible_comment` | 핵심 민원 데이터, AI 추론 결과, 관리자 확정 결과 |
| `complaint_attachments` | `complaint_id`, `file_name`, `mime_type`, `file_data` | 민원 첨부파일 저장 |
| `complaint_status_history` | `prev_status`, `new_status`, `prev_final_category`, `new_final_category`, `memo`, `changed_at` | 민원 처리 상태 및 관리자 수정 이력 |
| `statistics` | `stat_date`, `category`, `total_count`, `pending_count`, `completed_count` | 통계 집계 결과 |

---

## Acknowledgement

이 프로젝트는 아래 오픈소스 모델 및 라이브러리를 기반으로 합니다.

```
@misc{kobert,
  title        = {KoBERT},
  author       = {SK Telecom AI},
  howpublished = {\url{https://github.com/SKTBrain/KoBERT}}
}
```

```
@misc{huggingface_transformers,
  author       = {Wolf, Thomas and others},
  title        = {Transformers: State-of-the-Art Natural Language Processing},
  year         = {2020},
  howpublished = {\url{https://github.com/huggingface/transformers}}
}
```

- **KoBERT 분류 모델**: [`skt/kobert-base-v1`](https://huggingface.co/skt/kobert-base-v1) — Hugging Face `AutoTokenizer` / `AutoModelForSequenceClassification` 사용
- **보조 AI**: [Google Gemini API](https://ai.google.dev/) — 개인정보 마스킹, 감정 정제, JSON 구조화
- **프레임워크**: [Streamlit](https://streamlit.io/), [PyTorch](https://pytorch.org/), [Hugging Face Transformers](https://huggingface.co/docs/transformers)

---

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.

Team 숙크크(SCC)가 직접 작성한 소스 코드, 문서, 프롬프트, 예시 데이터셋은 MIT License 조건에 따라 재사용할 수 있습니다.

단, KoBERT base model, PyTorch, Hugging Face Transformers, Streamlit, Google Gemini API, Aiven MySQL 등 외부 모델·라이브러리·서비스는 각 프로젝트 또는 서비스의 라이선스와 이용약관을 따릅니다. API 키, DB 비밀번호, 배포용 모델 zip 파일 등 민감 정보와 대용량 산출물은 공개 저장소에 포함하지 않습니다.
