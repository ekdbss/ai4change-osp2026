"""
db.py
민원 데이터 저장/조회를 위한 DB 연동 모듈

팀 레포의 sql/ 스키마(complaints, complaint_status_history 테이블)에 맞춰 작성했습니다.
DB는 MySQL로 확정되었으므로 pymysql 드라이버를 사용합니다.

사전 준비:
    pip install pymysql

연결 정보는 환경변수로 관리합니다 (비밀번호를 코드에 직접 적지 않기 위함).
팀에서 공유받은 접속 정보로 아래 환경변수를 설정하세요.

    export DB_HOST=localhost
    export DB_PORT=3306
    export DB_USER=root
    export DB_PASSWORD=비밀번호
    export DB_NAME=scc_osp2026

로컬에 MySQL이 아직 없거나 우선 동작만 확인하고 싶다면, DATABASE_URL을 직접
SQLite로 지정해서 임시로 테스트할 수도 있습니다 (스키마는 동일하게 생성됨):

    export DATABASE_URL=sqlite:///complaints_test.db
"""

import os
import datetime
from typing import List, Optional

from sqlalchemy import (
    create_engine,
    Column,
    BigInteger,
    String,
    Text,
    Float,
    JSON,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker

# DATABASE_URL을 직접 지정하면 그게 최우선 (테스트용 SQLite 등)
# 아니면 DB_HOST 등 개별 환경변수로 MySQL 접속 문자열을 조립
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = os.environ.get("DB_PORT", "3306")
    db_user = os.environ.get("DB_USER", "root")
    db_password = os.environ.get("DB_PASSWORD", "")
    db_name = os.environ.get("DB_NAME", "scc_osp2026")
    DATABASE_URL = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    parent_type = Column(String(50), nullable=True)
    phone_masked = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Admin(Base):
    __tablename__ = "admins"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="teacher")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    original_text = Column(Text, nullable=False)         # 민원 원문
    masked_text = Column(Text, nullable=True)             # 개인정보 마스킹본 (Gemini 파이프라인에서 채움)
    refined_text = Column(Text, nullable=False)            # 감정 중립화된 정제본 (Gemini 파이프라인에서 채움)
    structured_json = Column(JSON, nullable=False)         # 행정 처리용 구조화 JSON (Gemini 파이프라인에서 채움)
    category = Column(String(50), nullable=False)          # KoBERT 분류 결과 (팀 공식 라벨 문자열)
    confidence = Column(Float, nullable=False)              # 분류 신뢰도 (0~100, %)
    status = Column(String(30), nullable=False, default="접수")
    recommended_department = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )


class ComplaintStatusHistory(Base):
    __tablename__ = "complaint_status_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    complaint_id = Column(BigInteger, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False)
    admin_id = Column(BigInteger, ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    prev_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=False)
    memo = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=datetime.datetime.utcnow)


def init_db() -> None:
    """테이블이 없으면 생성합니다. (이미 sql/ 스크립트로 생성돼 있다면 그냥 통과됨)"""
    Base.metadata.create_all(bind=engine)


def save_complaint(
    title: str,
    original_text: str,
    category: str,
    confidence: float,
    refined_text: Optional[str] = None,
    masked_text: Optional[str] = None,
    structured_json: Optional[dict] = None,
    user_id: Optional[int] = None,
    recommended_department: Optional[str] = None,
) -> int:
    """분류된 민원을 저장하고 새로 생성된 id를 반환합니다.

    refined_text / masked_text / structured_json은 Gemini 정제 파이프라인이
    채워주는 값입니다. 아직 그쪽 연동 전이라면 None으로 두고 우선 저장할 수 있도록
    refined_text가 비어 있으면 original_text로 대체합니다 (DB의 NOT NULL 제약 때문).
    """
    session = SessionLocal()
    try:
        complaint = Complaint(
            title=title,
            original_text=original_text,
            masked_text=masked_text,
            refined_text=refined_text or original_text,
            structured_json=structured_json or {},
            category=category,
            confidence=confidence,
            recommended_department=recommended_department,
            user_id=user_id,
        )
        session.add(complaint)
        session.commit()
        session.refresh(complaint)
        return complaint.id
    finally:
        session.close()


def get_all_complaints(category: Optional[str] = None, status: Optional[str] = None) -> List[dict]:
    """민원 목록을 최신순으로 반환합니다 (관리자 대시보드용)."""
    session = SessionLocal()
    try:
        query = session.query(Complaint).order_by(Complaint.created_at.desc())
        if category:
            query = query.filter(Complaint.category == category)
        if status:
            query = query.filter(Complaint.status == status)
        rows = query.all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "original_text": r.original_text,
                "masked_text": r.masked_text,
                "refined_text": r.refined_text,
                "structured_json": r.structured_json,
                "category": r.category,
                "confidence": r.confidence,
                "status": r.status,
                "recommended_department": r.recommended_department,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
            }
            for r in rows
        ]
    finally:
        session.close()


def update_status(
    complaint_id: int,
    new_status: str,
    admin_id: Optional[int] = None,
    memo: Optional[str] = None,
) -> None:
    """선생님이 민원 상태를 변경할 때 호출합니다. 변경 이력도 같이 남깁니다."""
    session = SessionLocal()
    try:
        complaint = session.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            return
        prev_status = complaint.status
        complaint.status = new_status
        session.add(
            ComplaintStatusHistory(
                complaint_id=complaint_id,
                admin_id=admin_id,
                prev_status=prev_status,
                new_status=new_status,
                memo=memo,
            )
        )
        session.commit()
    finally:
        session.close()
