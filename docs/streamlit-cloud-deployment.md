# Streamlit Cloud Deployment Guide

## 1. 배포 구조

Streamlit Cloud 서버는 로컬 PC의 `.env`, MySQL, `kobert_v1_1800.zip` 파일을 자동으로 가져가지 않는다.
따라서 배포 시에는 아래 3가지를 별도로 준비한다.

- Gemini API Key: Streamlit Cloud Secrets에 저장
- MySQL: Railway, Aiven, AWS RDS 등 외부에서 접속 가능한 MySQL 사용
- KoBERT 모델: GitHub Releases, Hugging Face, Google Drive 직접 다운로드 링크 등에 zip으로 업로드

## 2. KoBERT 모델 업로드

Colab에서 받은 `kobert_v1_1800.zip`을 배포용 파일 저장소에 업로드한다.

권장 방법:

1. GitHub 저장소의 Releases 메뉴로 이동
2. 새 Release 생성
3. `kobert_v1_1800.zip`을 Release asset으로 업로드
4. 업로드된 asset의 다운로드 URL을 복사
5. Streamlit Cloud Secrets의 `KOBERT_MODEL_ZIP_URL`에 붙여넣기

선택적으로 SHA256 검증값도 넣을 수 있다.

```powershell
Get-FileHash .\kobert_v1_1800.zip -Algorithm SHA256
```

출력된 해시값을 `KOBERT_MODEL_ZIP_SHA256`에 넣으면, Cloud에서 다운로드한 zip이 원본과 같은지 확인한다.

## 3. Streamlit Cloud Secrets

Streamlit Cloud의 App settings > Secrets에 아래 형식으로 입력한다.

```toml
GEMINI_API_KEY = "replace-with-your-gemini-api-key"

DB_HOST = "replace-with-external-mysql-host"
DB_PORT = "3306"
DB_USER = "replace-with-db-user"
DB_PASSWORD = "replace-with-db-password"
DB_NAME = "scc_osp2026"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "replace-with-admin-password"

KOBERT_MODEL_ZIP_URL = "https://example.com/kobert_v1_1800.zip"
KOBERT_MODEL_ZIP_SHA256 = ""
```

`KOBERT_MODEL_ZIP_SHA256`은 선택값이다. 비워두면 해시 검증 없이 설치한다.

## 4. 외부 MySQL 준비

로컬 MySQL Workbench의 DB는 Streamlit Cloud에서 접근할 수 없다.
배포 시에는 외부 MySQL 인스턴스가 필요하다.

최소 준비 항목:

- MySQL host
- port
- user
- password
- database name
- 외부 접속 허용 설정

DB를 만든 뒤 `sql/schema.sql`을 실행한다.

## 5. 배포 후 확인 순서

1. Streamlit Cloud에서 앱 배포
2. 학부모 로그인
3. 민원 내용 입력
4. AI 정제 미리보기 실행
5. 화면에 `직접 Fine-Tuning한 KoBERT 모델이 카테고리/긴급도 판단에 사용되었습니다.` 문구 확인
6. 민원 접수
7. 관리자 로그인
8. 접수된 민원이 외부 MySQL에 저장되었는지 확인
9. 관리자 화면의 `KoBERT 학습 모델 상태`에서 모델 연결 상태 확인
10. 모델 리포트 페이지에서 학습 데이터 1,800건 및 평가 결과 확인

## 6. 실패 시 빠른 판단

- KoBERT 모델이 연결되지 않음: `KOBERT_MODEL_ZIP_URL`이 직접 다운로드 가능한 URL인지 확인
- Gemini 정제가 데모로 표시됨: `GEMINI_API_KEY` 확인
- 민원이 저장되지 않음: 외부 MySQL 접속 정보, 방화벽, `sql/schema.sql` 실행 여부 확인
- STT 녹음 변환 실패: Gemini API 할당량 확인. 브라우저 받아쓰기 패널은 API 없이 대체 사용 가능
