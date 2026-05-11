# ai4change-osp2026

AI 기술을 활용하여 사회적 문제를 해결하는 서비스 프로젝트  
Open Source Programming Team Project (2026-1)

---

# 📌 Initial Project Topic (Archived)

## 🧓 AI 기반 노인 고독사 예방 감정 분석 앱

초기 프로젝트 기획 단계에서는  
고령화 사회에서 증가하는 독거노인 문제와 고독사 위험에 주목하여,  
AI 기반 감정 분석 서비스를 기획하였다.

사용자의 음성을 기록하고 감정을 분석하여  
정서적 위험 신호를 조기에 탐지하는 것을 목표로 하였다.

---

# 📖 Background

한국은 초고령사회에 진입하면서  
독거노인 및 고독사 문제가 빠르게 증가하고 있다.

기존 복지 시스템은 다음과 같은 한계를 가진다.

- 복지사 방문은 월 1~2회 수준
- 실시간 감정 상태 파악의 어려움
- IoT 기반 시스템은 움직임 중심 감지만 가능
- 정서적 위험 신호를 지속적으로 분석하기 어려움

이에 따라 AI 기반 감정 분석 기술을 활용하여  
노인의 정서 상태를 지속적으로 분석하는 서비스를 제안하였다.

---

# 🎯 Objectives

- 음성 기반 감정 기록 시스템 구축
- AI 기반 감정 분석 모델 적용
- 위험 신호 조기 탐지 시스템 설계
- 보호자 및 복지사 대응 지원
- 사회적 고립 문제 해결 가능성 탐색

---

# 🧠 Core Features

## 사용자 기능

- STT 기반 음성 일기 작성
- 감정 분석 결과 제공
- 감정 변화 그래프 시각화
- 위험도 표시 기능

## 보호자 기능

- 위험도 HIGH 발생 시 알림
- 감정 변화 추이 확인

---

# ⚙️ Planned AI Pipeline

```text
사용자 음성 입력
        ↓
STT 변환
        ↓
한국어 감정 분석 모델
        ↓
위험도 계산
        ↓
감정 리포트 생성
```

---

# 🧠 Planned AI Model

## Model

- KoELECTRA
- `monologg/koelectra-base-v3-discriminator`

## Expected Tasks

- 긍정 / 부정 / 중립 감정 분류
- 세부 감정 분석
  - 우울
  - 외로움
  - 불안
  - 슬픔
  - 기쁨 등
- 위험도 점수 계산

---

# 🗂 Dataset Research

프로젝트 기획 단계에서 다음 데이터셋 활용을 검토하였다.

- AIHub 감정 분석 말뭉치
- 감성 대화 말뭉치
- 웰니스 대화 데이터
- KLUE-TC

또한 노인 말투 기반 데이터셋 구축 가능성도 함께 조사하였다.

---

# 🏗 Planned Architecture

```text
[ User App ]
      ↓
[ React Native Frontend ]
      ↓
[ FastAPI Backend ]
      ↓
[ AI Inference Server ]
      ↓
[ Fine-tuned KoELECTRA ]
      ↓
[ PostgreSQL ]
```

---

# 🛠️ Planned Tech Stack

## Frontend

- React Native
- Tailwind CSS
- Chart.js

## Backend

- FastAPI
- REST API
- JWT Authentication

## AI

- PyTorch
- Transformers
- KoELECTRA

## Database

- PostgreSQL
- SQLAlchemy

---

# 🔄 Project Direction Change

프로젝트 초기 기획 과정에서  
AI 기반 감정 분석을 활용한 사회 문제 해결 가능성을 탐색하였다.

이후 팀 논의를 통해:

- 실제 구현 가능성
- 데이터 수집 난이도
- 서비스 범위 구체화
- 제한된 개발 기간 내 완성도 확보

등을 종합적으로 고려하여  
현재 프로젝트 방향으로 주제를 재정비하였다.

본 README는 초기 기획 및 아이디어 탐색 과정을 기록하기 위해 보존한다.

---

# 👥 Team Members

| Name | Role |
|---|---|
| 김다윤 | TBD |
| 김서현 | TBD |
| 한예진 | TBD |

---

# 📂 Project Structure

```text
ai4change-osp2026/
├── backend/
├── frontend/
├── model/
├── data/
└── README.md
```
