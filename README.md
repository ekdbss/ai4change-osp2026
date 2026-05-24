# 🏫 학교 민원 AI 정제 서비스
### Team 숙크크(SCC) | Open Source Programming Team Project (2026-1)
![Status](https://img.shields.io/badge/status-active-brightgreen)
![AI](https://img.shields.io/badge/AI-Gemini-blue)
![Frontend](https://img.shields.io/badge/frontend-Streamlit-orange)
![Backend](https://img.shields.io/badge/backend-Python-yellow)
![Database](https://img.shields.io/badge/database-MongoDB-green)
![Deployment](https://img.shields.io/badge/deploy-Streamlit%20Cloud-lightgrey)

> 감정적인 학교 민원을 AI가 정제하고 구조화하여  
> 학교가 핵심 내용을 빠르게 파악할 수 있도록 돕는 웹 서비스
> AI 기반 감정 정제 및 민원 구조화를 통해  
> 학교 민원 처리 과정을 개선하는 스마트 민원 플랫폼

---

## 📌 Project Overview

최근 학교 민원 건수가 지속적으로 증가하면서  
교사의 감정노동 및 민원 스트레스 문제가 사회적 이슈로 떠오르고 있다.

특히 기존 전화 중심 민원 시스템은 다음과 같은 구조적 문제를 가진다:

- 감정적 표현 전달로 인한 오해 발생
- 사실관계 파악의 어려움
- 기록 및 데이터 관리 한계
- 담당자 부재 시 처리 지연

본 프로젝트는 생성형 AI를 활용하여  
감정적인 민원 표현을 사실 중심의 문장으로 정제하고,  
민원 내용을 구조화하여 학교 담당자가 보다 효율적으로 민원을 처리할 수 있도록 돕는 서비스이다.

---

## 🎯 Objectives

- AI 기반 감정 정제 시스템 구현
- 학교 민원 자동 구조화 기능 개발
- 교사 감정노동 감소 및 교권 보호
- 학부모-학교 간 갈등 완화
- 접근성을 고려한 사용자 경험 제공

---

## 📊 Scope Definition (중요)

### 🧠 Project Scope (기획 범위)
- 음성 + 텍스트 기반 민원 입력
- AI 기반 감정 정제
- 민원 자동 구조화
- 관리자용 결과 확인 시스템
- 확장 가능 구조 설계 (STT / 통계 / 분석)

---

### ⚙️ Implementation Scope (구현 범위 - MVP)

현재 실제 구현 범위는 다음과 같다:

- 텍스트 기반 민원 입력
- Gemini API 기반 감정 정제
- JSON 형태 민원 구조화
- 기본 관리자 UI (Streamlit)
- DB 저장 기능

---

## 💡 Core Idea

사용자가 민원을 입력하면 AI가 다음 과정을 수행한다:

1. 감정적 표현 완화
2. 핵심 내용 추출
3. 구조화된 데이터 생성
4. 관리자 화면 제공

이를 통해:
- 학부모는 명확하게 의견 전달
- 학교는 빠르게 핵심 파악 가능

---

## 🧠 Key Features

### ✅ AI 감정 정제
감정적 표현을 공손하고 객관적인 문장으로 변환

```text
원문:
"왜 이렇게 처리 안 하세요? 너무 화납니다."

결과:
"해당 사안에 대한 확인 및 조치를 요청드립니다."
```
---

## 🌿 Git Branch Strategy

```text
main
└── develop
    ├── feature/frontend-parent
    ├── feature/prompt-engineering
    └── feature/backend-core
```
- `main` : 최종 배포 브랜치
- `develop` : 통합 개발 브랜치
- `feature/*` : 기능 단위 작업 브랜치