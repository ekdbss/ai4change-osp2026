# 학교 민원 AI 정제 및 자동 분류 플랫폼

#### Team 숙크크(SCC) Open Source Programming Team Project 2026-1


AI 기반 학부모 민원 관리 플랫폼 | Open-Source Project 2026

---

## 프로젝트 개요

**SCC**는 학부모 민원을 디지털로 접수하고, 팀이 직접 파인튜닝(Fine-Tuning)한 KoBERT 모델로 민원 카테고리를 자동 분류하는 웹 플랫폼입니다.

분류된 데이터는 Gemini API를 보조 AI로 활용하여 감정 표현을 정제하고, 행정 처리용 JSON으로 구조화합니다.
단순 생성형 AI API 호출을 넘어, **직접 학습시킨 분류 모델을 서비스 파이프라인에 통합**한 것이 핵심입니다.

### 주요 기능

- 학부모 민원 디지털 접수 및 개인정보 마스킹(PII Masking)
- KoBERT 파인튜닝 모델을 통한 민원 카테고리 자동 분류
- Gemini API 기반 감정 중립화 및 행정 처리용 JSON 구조화
- 교사/관리자용 대시보드 및 처리 상태 이력 관리
- 분류 모델 성능 리포트 페이지

---

## 파이프라인 구조

```
학부모 민원 입력
      │
      ▼
PII 마스킹 (pii_masker.py)
      │
      ▼
KoBERT 카테고리 분류 (kobert_predictor.py)
      │
      ▼
Gemini 감정 정제 + JSON 구조화 (gemini_service.py)
      │
      ▼
MySQL DB 저장 (complaint_repository.py)
      │
      ▼
관리자 대시보드 (admin_dashboard.py)
```

---

## 프로젝트 구조

```
.
├── README.md
├── app.py                          # Streamlit 엔트리포인트
├── classifier.py                   # 분류 파이프라인 통합
├── db.py                           # DB 연결 설정
├── requirements.txt
│
├── data/
│   ├── raw/
│   │   ├── generated_complaints.csv        # 학습용 합성 데이터
│   │   └── generated_complaints_backup.csv
│   └── processed/                          # 전처리된 데이터 저장 경로
│
├── model/
│   ├── train_kobert.py             # KoBERT 파인튜닝 학습 스크립트
│   ├── dataset.py                  # 커스텀 Dataset 클래스
│   ├── evaluate.py                 # 모델 평가 스크립트
│   └── saved_model/                # 파인튜닝된 모델 저장 경로 (아래 참고)
│       ├── config.json
│       ├── label_map.json
│       ├── model.safetensors
│       ├── tokenizer.json
│       ├── tokenizer_config.json
│       └── training_args.bin
│
├── pages/                          # Streamlit 멀티페이지
│   ├── 1_submit_complaint.py       # 민원 접수 페이지 (학부모)
│   ├── 2_admin_dashboard.py        # 관리자 대시보드
│   ├── 3_statistics.py             # 통계 시각화
│   └── 4_model_report.py           # 분류 모델 성능 리포트
│
├── prompts/                        # Gemini 프롬프트 템플릿
│   ├── data_generation_prompt.md
│   ├── gemini_refine_prompt.md
│   └── gemini_structure_prompt.md
│
├── scripts/
│   └── generate_synthetic_data.py  # 합성 학습 데이터 생성 스크립트
│
├── sql/
│   ├── schema.sql                  # DB 테이블 생성 스크립트
│   └── seed_admin.sql              # 초기 관리자 계정 시드 데이터
│
└── src/
    ├── ai/
    │   ├── gemini_service.py       # Gemini API 호출 (정제 + 구조화)
    │   ├── kobert_predictor.py     # KoBERT 추론 모듈
    │   └── pii_masker.py           # 개인정보 마스킹
    ├── db/
    │   ├── complaint_repository.py # 민원 CRUD
    │   └── connection.py           # DB 연결 풀
    └── services/
        ├── complaint_service.py    # 비즈니스 로직
        └── session_store.py        # 세션 상태 관리
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
| Frontend | `streamlit` | `>=1.35.0` |
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

```
# .env.example
DB_HOST=localhost
DB_PORT=3306
DB_NAME=scc_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password

GEMINI_API_KEY=your_gemini_api_key
```

### 4. 데이터베이스 초기화

MySQL이 설치된 상태에서 아래 스크립트를 순서대로 실행합니다.

```bash
# 테이블 생성
mysql -u your_db_user -p scc_db < sql/schema.sql

# 초기 관리자 계정 삽입
mysql -u your_db_user -p scc_db < sql/seed_admin.sql
```

> 로컬 테스트 시 `.env`에 `DATABASE_URL=sqlite:///complaints_test.db`를 추가하면
> SQLite로 동작합니다. (단, `db.py` 경유 기능만 해당. `connection.py`는 MySQL 전용)

### 5. 모델 파일 준비

파인튜닝된 KoBERT 모델 파일을 `model/saved_model/` 경로에 위치시킵니다.

```
model/saved_model/
├── config.json 
├── label_map.json
├── model.safetensors
├── tokenizer.json
├── tokenizer_config.json
└── training_args.bin
```

> 모델 파일은 용량 문제로 Git LFS로 관리됩니다. 아래 명령어로 받아오세요.
> ```bash
> git lfs pull
> ```

### 6. 앱 실행

```bash
streamlit run app.py

# 또는 모듈 방식으로 실행 (환경에 따라)
python -m streamlit run app.py
```

---

## 학습 데이터

합성 데이터는 `scripts/generate_synthetic_data.py`로 생성할 수 있습니다.

```bash
python scripts/generate_synthetic_data.py
```

생성된 CSV 파일은 `data/raw/generated_complaints.csv`에 저장됩니다.

| 경로 | 설명 |
|------|------|
| `data/raw/generated_complaints.csv` | 학습용 합성 민원 데이터 |
| `data/raw/generated_complaints_backup.csv` | 백업본 |
| `data/processed/` | 전처리 완료 데이터 저장 경로 |

---

## KoBERT 모델 학습

```bash
python model/train_kobert.py
```

학습 완료 후 모델은 자동으로 `model/saved_model/`에 저장됩니다.

모델 평가:

```bash
python model/evaluate.py
```

---

## DB 스키마

총 4개의 핵심 테이블로 구성됩니다. 자세한 DDL은 `sql/schema.sql`을 참고하세요.

| 테이블 | 주요 컬럼 | 설명 |
|--------|-----------|------|
| `users` | `id`, `parent_type`, `phone_masked` | 학부모 식별 정보 |
| `admins` | `username`, `role` | 교사/관리자 계정 |
| `complaints` | `original_text`, `masked_text`, `refined_text`, `structured_json`, `category`, `confidence`, `status`, `recommended_department` | 핵심 민원 데이터 및 AI 추론 결과 |
| `complaint_status_history` | `prev_status`, `new_status`, `memo` | 민원 처리 상태 변경 이력 |

---

## Acknowledgement

이 프로젝트는 아래 오픈소스 모델 및 라이브러리를 기반으로 합니다.

```
@misc{klue,
  title        = {KLUE: Korean Language Understanding Evaluation},
  author       = {Park, Sungjoon and others},
  year         = {2021},
  howpublished = {\url{https://github.com/KLUE-benchmark/KLUE}}
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

- **KoBERT 분류 모델**: [`klue/bert-base`](https://huggingface.co/klue/bert-base) — Hugging Face `AutoTokenizer` / `AutoModelForSequenceClassification` 사용
- **보조 AI**: [Google Gemini API](https://ai.google.dev/) — 개인정보 마스킹, 감정 정제, JSON 구조화
- **프레임워크**: [Streamlit](https://streamlit.io/), [PyTorch](https://pytorch.org/), [Hugging Face Transformers](https://huggingface.co/docs/transformers)

---

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.
