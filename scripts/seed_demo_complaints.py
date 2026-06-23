from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.db.connection import get_connection


SCHOOL_NAME = "새봄초등학교"
REGION_NAME = "서울특별시교육청"

PARENTS = [
    {
        "parent_name": "김병규",
        "parent_type": "부",
        "phone_tail": "1234",
        "student_grade": "3학년",
        "student_class": "2반",
        "student_number": "15",
        "student_name": "김민준",
    },
    {
        "parent_name": "이서연",
        "parent_type": "모",
        "phone_tail": "5678",
        "student_grade": "4학년",
        "student_class": "1반",
        "student_number": "8",
        "student_name": "박지우",
    },
    {
        "parent_name": "박현수",
        "parent_type": "보호자",
        "phone_tail": "2468",
        "student_grade": "5학년",
        "student_class": "3반",
        "student_number": "21",
        "student_name": "최하준",
    },
]

DEPARTMENT_BY_CATEGORY = {
    "수업/학습 문제": "교무부",
    "교사 태도/행동": "교무부",
    "시설/환경": "시설관리",
    "급식": "급식실",
    "생활지도/안전": "생활안전부",
    "기타": "행정실",
}

PRIORITY_BY_URGENCY = {
    "높음": 1,
    "보통": 3,
    "낮음": 4,
}

DEMO_COMPLAINTS = [
    {
        "parent_index": 0,
        "category": "수업/학습 문제",
        "urgency": "보통",
        "status": "접수",
        "days_ago": 13,
        "title": "수학 수업 질문 응대 확인 요청",
        "original_text": "수학 시간에 아이가 질문했는데 진도가 늦어진다며 넘어갔다고 합니다. 이해하지 못한 부분을 확인할 수 있는 시간이 필요합니다.",
        "refined_text": "수학 수업 중 학생의 질문이 충분히 다루어졌는지 확인을 요청드리며, 보충 질의응답 방법 안내를 부탁드립니다.",
        "comment": "",
    },
    {
        "parent_index": 1,
        "category": "수업/학습 문제",
        "urgency": "낮음",
        "status": "처리 완료",
        "days_ago": 28,
        "title": "과제 제출 안내 방식 개선 요청",
        "original_text": "과제 제출 공지가 늦게 올라와 아이가 준비에 어려움을 겪었습니다. 제출 기준을 조금 더 일찍 안내해 주세요.",
        "refined_text": "과제 제출 일정과 기준이 충분히 사전에 안내될 수 있도록 공지 방식 개선을 요청드립니다.",
        "comment": "과제 안내는 다음 주부터 금요일 주간 안내문에 함께 공지하도록 조정했습니다.",
    },
    {
        "parent_index": 2,
        "category": "교사 태도/행동",
        "urgency": "높음",
        "status": "검토 중",
        "days_ago": 9,
        "title": "학생 공개 지적 관련 상담 요청",
        "original_text": "아이 말로는 친구들 앞에서 공개적으로 지적을 받아 많이 위축되었다고 합니다. 사실관계를 확인하고 상담을 부탁드립니다.",
        "refined_text": "학생이 공개적인 지적으로 심리적 위축을 느낀 상황이 있었는지 확인하고, 학생 상담 및 재발 방지 검토를 요청드립니다.",
        "comment": "담임교사와 상담 일정을 조율 중이며, 학생의 심리적 부담을 우선 확인하겠습니다.",
    },
    {
        "parent_index": 0,
        "category": "교사 태도/행동",
        "urgency": "보통",
        "status": "보류",
        "days_ago": 36,
        "title": "학부모 상담 답변 지연 문의",
        "original_text": "상담 요청 메일을 보냈는데 답변이 늦어지고 있습니다. 확인 후 연락 부탁드립니다.",
        "refined_text": "학부모 상담 요청에 대한 답변 지연 여부를 확인하고, 가능한 상담 일정 안내를 요청드립니다.",
        "comment": "담당 교사의 출장 일정 확인 후 상담 가능 시간을 다시 안내드리겠습니다.",
    },
    {
        "parent_index": 1,
        "category": "시설/환경",
        "urgency": "높음",
        "status": "검토 중",
        "days_ago": 7,
        "title": "체육관 바닥 미끄럼 안전 점검 요청",
        "original_text": "체육관 바닥이 미끄러워 아이들이 넘어질 뻔했다고 합니다. 안전 점검이 필요합니다.",
        "refined_text": "체육관 바닥 미끄럼으로 인한 안전사고 위험 여부를 점검하고 필요한 조치를 요청드립니다.",
        "comment": "시설관리 담당자가 현장 확인을 진행하고 있으며, 임시 미끄럼 주의 안내를 부착했습니다.",
    },
    {
        "parent_index": 2,
        "category": "시설/환경",
        "urgency": "보통",
        "status": "접수",
        "days_ago": 21,
        "title": "교실 냉난방 온도 조정 문의",
        "original_text": "교실이 너무 추워 아이가 수업 중 계속 겉옷을 입고 있다고 합니다. 온도 기준을 확인해 주세요.",
        "refined_text": "교실 냉난방 온도 운영 기준을 확인하고, 학생들이 수업에 집중할 수 있는 환경 조정을 요청드립니다.",
        "comment": "",
    },
    {
        "parent_index": 0,
        "category": "급식",
        "urgency": "높음",
        "status": "검토 중",
        "days_ago": 4,
        "title": "급식 알레르기 표시 확인 요청",
        "original_text": "알레르기 표시가 잘 보이지 않아 아이가 불안해합니다. 알레르기 식품 표시를 더 명확하게 해주세요.",
        "refined_text": "급식 알레르기 유발 식품 표시가 학생에게 명확히 전달되는지 확인하고, 표시 방식 개선을 요청드립니다.",
        "comment": "영양교사와 급식실에서 알레르기 표시 위치와 글자 크기를 점검하고 있습니다.",
    },
    {
        "parent_index": 1,
        "category": "급식",
        "urgency": "보통",
        "status": "처리 완료",
        "days_ago": 18,
        "title": "급식 배식 온도 개선 요청",
        "original_text": "국과 반찬이 식어서 제공되는 날이 많다고 합니다. 배식 온도를 확인해 주세요.",
        "refined_text": "급식 배식 시 음식 온도가 적절히 유지되는지 확인하고, 배식 절차 개선을 요청드립니다.",
        "comment": "급식실 배식 순서와 보온 장비 점검을 완료했으며, 지속적으로 모니터링하겠습니다.",
    },
    {
        "parent_index": 2,
        "category": "생활지도/안전",
        "urgency": "높음",
        "status": "접수",
        "days_ago": 2,
        "title": "하교 시간 교문 앞 안전지도 요청",
        "original_text": "하교 시간에 차량과 학생들이 뒤섞여 위험해 보입니다. 교문 앞 안전지도가 필요합니다.",
        "refined_text": "하교 시간 교문 앞 학생 보행 안전과 차량 동선 관리를 확인하고, 안전지도 강화를 요청드립니다.",
        "comment": "",
    },
    {
        "parent_index": 0,
        "category": "생활지도/안전",
        "urgency": "높음",
        "status": "검토 중",
        "days_ago": 31,
        "title": "복도 뛰어다님 생활지도 요청",
        "original_text": "쉬는 시간 복도에서 뛰는 학생들이 많아 충돌 위험이 있습니다. 생활지도를 강화해 주세요.",
        "refined_text": "쉬는 시간 복도 이동 안전과 학생 충돌 위험 여부를 확인하고, 생활지도 강화를 요청드립니다.",
        "comment": "학년부에서 쉬는 시간 복도 순회 지도를 확대했습니다.",
    },
    {
        "parent_index": 1,
        "category": "기타",
        "urgency": "낮음",
        "status": "처리 완료",
        "days_ago": 45,
        "title": "가정통신문 앱 알림 지연 문의",
        "original_text": "가정통신문 앱 알림이 늦게 와서 준비물을 놓치는 경우가 있습니다. 알림 발송 상태를 확인해 주세요.",
        "refined_text": "가정통신문 앱 알림 지연 여부를 확인하고, 공지 전달 방식의 안정성 점검을 요청드립니다.",
        "comment": "알림 앱 설정과 발송 시간을 점검했으며, 중요 공지는 문자 안내를 병행하겠습니다.",
    },
    {
        "parent_index": 2,
        "category": "기타",
        "urgency": "보통",
        "status": "보류",
        "days_ago": 56,
        "title": "방과후 프로그램 신청 방식 문의",
        "original_text": "방과후 프로그램 신청이 너무 빨리 마감되어 신청하기 어렵습니다. 신청 방식 개선을 검토해 주세요.",
        "refined_text": "방과후 프로그램 신청 과정에서 접근성 문제가 있는지 확인하고, 신청 방식 개선 검토를 요청드립니다.",
        "comment": "다음 학기 수요조사 결과와 시스템 가능 여부를 함께 검토하겠습니다.",
    },
    {
        "parent_index": 0,
        "category": "시설/환경",
        "urgency": "낮음",
        "status": "처리 완료",
        "days_ago": 62,
        "title": "도서관 의자 교체 건의",
        "original_text": "도서관 의자가 오래되어 삐걱거립니다. 학생들이 조용히 공부할 수 있도록 교체를 검토해 주세요.",
        "refined_text": "도서관 의자 노후 상태를 확인하고, 학생 학습 환경 개선을 위한 교체 검토를 요청드립니다.",
        "comment": "노후 의자 12개를 우선 교체했고, 나머지는 예산 범위에서 순차 교체 예정입니다.",
    },
    {
        "parent_index": 1,
        "category": "급식",
        "urgency": "낮음",
        "status": "접수",
        "days_ago": 66,
        "title": "급식 메뉴 다양화 건의",
        "original_text": "비슷한 메뉴가 자주 나와 아이가 급식에 흥미를 잃고 있습니다. 메뉴 다양화를 검토해 주세요.",
        "refined_text": "급식 메뉴 구성의 다양성을 검토하고, 학생 선호도 반영 가능 여부 확인을 요청드립니다.",
        "comment": "",
    },
    {
        "parent_index": 2,
        "category": "수업/학습 문제",
        "urgency": "보통",
        "status": "검토 중",
        "days_ago": 73,
        "title": "수행평가 기준 안내 요청",
        "original_text": "수행평가 기준을 아이가 정확히 이해하지 못해 준비가 어렵다고 합니다. 평가 기준 안내를 부탁드립니다.",
        "refined_text": "수행평가 기준이 학생에게 충분히 안내되었는지 확인하고, 구체적인 평가 기준 재안내를 요청드립니다.",
        "comment": "교과 담당 교사가 평가 기준표를 다시 안내할 예정입니다.",
    },
    {
        "parent_index": 0,
        "category": "교사 태도/행동",
        "urgency": "낮음",
        "status": "접수",
        "days_ago": 81,
        "title": "상담 일정 조율 요청",
        "original_text": "담임 상담 시간이 맞지 않아 일정을 다시 잡고 싶습니다. 가능한 시간을 알려주세요.",
        "refined_text": "담임 상담 일정 재조율 가능 여부를 확인하고, 가능한 상담 시간을 안내해 주시기 바랍니다.",
        "comment": "",
    },
    {
        "parent_index": 1,
        "category": "생활지도/안전",
        "urgency": "보통",
        "status": "처리 완료",
        "days_ago": 88,
        "title": "자전거 통학 안전 안내 요청",
        "original_text": "자전거로 등교하는 학생들이 헬멧을 쓰지 않는 경우가 많습니다. 안전 안내가 필요합니다.",
        "refined_text": "자전거 통학 학생의 보호장구 착용 여부를 확인하고, 교통안전 안내 강화를 요청드립니다.",
        "comment": "전교생 안전교육 시간에 자전거 통학 안전 수칙을 안내했습니다.",
    },
    {
        "parent_index": 2,
        "category": "기타",
        "urgency": "낮음",
        "status": "검토 중",
        "days_ago": 96,
        "title": "학교 홈페이지 공지 검색 개선 건의",
        "original_text": "학교 홈페이지에서 예전 공지를 찾기가 어렵습니다. 검색 기능이나 분류를 개선해 주세요.",
        "refined_text": "학교 홈페이지 공지 검색과 분류 체계의 사용성을 점검하고, 개선 가능 여부 검토를 요청드립니다.",
        "comment": "행정실에서 홈페이지 게시판 분류 체계를 검토하고 있습니다.",
    },
]


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def build_parent_login_id(parent: dict) -> str:
    raw = "|".join(
        [
            parent["parent_name"],
            parent["phone_tail"],
            SCHOOL_NAME,
            parent["student_grade"],
            parent["student_class"],
            parent["student_number"],
            parent["student_name"],
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def insert_admin(cursor) -> int:
    cursor.execute(
        """
        INSERT INTO admins (username, password_hash, display_name, role, region_name, school_name)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            password_hash = VALUES(password_hash),
            display_name = VALUES(display_name),
            role = VALUES(role),
            region_name = VALUES(region_name),
            school_name = VALUES(school_name)
        """,
        ("admin", hash_password("admin1234"), "데모 관리자", "admin", REGION_NAME, SCHOOL_NAME),
    )
    cursor.execute("SELECT id FROM admins WHERE username = %s", ("admin",))
    return int(cursor.fetchone()["id"])


def insert_parents(cursor) -> list[int]:
    user_ids = []
    for parent in PARENTS:
        login_id = build_parent_login_id(parent)
        cursor.execute(
            """
            INSERT INTO users (
                login_id,
                parent_name,
                parent_type,
                phone_masked,
                school_name,
                student_grade,
                student_class,
                student_number,
                student_name
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                parent_name = VALUES(parent_name),
                parent_type = VALUES(parent_type),
                phone_masked = VALUES(phone_masked),
                school_name = VALUES(school_name),
                student_grade = VALUES(student_grade),
                student_class = VALUES(student_class),
                student_number = VALUES(student_number),
                student_name = VALUES(student_name)
            """,
            (
                login_id,
                parent["parent_name"],
                parent["parent_type"],
                f"***-****-{parent['phone_tail']}",
                SCHOOL_NAME,
                parent["student_grade"],
                parent["student_class"],
                parent["student_number"],
                parent["student_name"],
            ),
        )
        cursor.execute("SELECT id FROM users WHERE login_id = %s", (login_id,))
        user_ids.append(int(cursor.fetchone()["id"]))
    return user_ids


def build_structured_json(item: dict) -> str:
    return json.dumps(
        {
            "summary": item["refined_text"][:90],
            "request": "관련 내용 확인 및 필요한 조치를 요청합니다.",
            "urgency": item["urgency"],
            "stakeholders": ["학부모", "학생", "학교 담당자"],
            "incident_date": "",
            "recommended_department": DEPARTMENT_BY_CATEGORY[item["category"]],
        },
        ensure_ascii=False,
    )


def insert_complaints(cursor, user_ids: list[int], admin_id: int) -> None:
    base_date = datetime.now().replace(hour=9, minute=20, second=0, microsecond=0)
    for index, item in enumerate(DEMO_COMPLAINTS, start=1):
        parent = PARENTS[item["parent_index"]]
        category = item["category"]
        urgency = item["urgency"]
        department = DEPARTMENT_BY_CATEGORY[category]
        created_at = base_date - timedelta(days=item["days_ago"], hours=index % 5)
        updated_at = created_at + timedelta(days=1 if item["status"] != "접수" else 0, hours=2)
        comment = item["comment"]

        cursor.execute(
            """
            INSERT INTO complaints (
                user_id,
                school_name,
                student_grade,
                student_class,
                student_number,
                student_name,
                title,
                original_text,
                masked_text,
                refined_text,
                structured_json,
                ai_category,
                final_category,
                ai_confidence,
                ai_urgency,
                final_urgency,
                urgency_confidence,
                priority_level,
                status,
                recommended_department,
                parent_visible_comment,
                created_at,
                updated_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            """,
            (
                user_ids[item["parent_index"]],
                SCHOOL_NAME,
                parent["student_grade"],
                parent["student_class"],
                parent["student_number"],
                parent["student_name"],
                item["title"],
                item["original_text"],
                item["original_text"],
                item["refined_text"],
                build_structured_json(item),
                category,
                category,
                round(0.78 + (index % 12) * 0.015, 4),
                urgency,
                urgency,
                round(0.72 + (index % 10) * 0.018, 4),
                PRIORITY_BY_URGENCY[urgency],
                item["status"],
                department,
                comment,
                created_at,
                updated_at,
            ),
        )
        complaint_id = int(cursor.lastrowid)

        cursor.execute(
            """
            INSERT INTO complaint_status_history (
                complaint_id,
                admin_id,
                prev_status,
                new_status,
                prev_final_category,
                new_final_category,
                prev_final_urgency,
                new_final_urgency,
                prev_priority_level,
                new_priority_level,
                memo,
                is_parent_visible,
                changed_at
            )
            VALUES (%s, %s, NULL, %s, NULL, %s, NULL, %s, NULL, %s, %s, TRUE, %s)
            """,
            (
                complaint_id,
                admin_id,
                item["status"],
                category,
                urgency,
                PRIORITY_BY_URGENCY[urgency],
                comment or "민원이 접수되었습니다.",
                updated_at,
            ),
        )


def print_summary(cursor) -> None:
    cursor.execute("SELECT COUNT(*) AS count FROM complaints")
    print(f"complaints: {cursor.fetchone()['count']}")

    cursor.execute(
        """
        SELECT final_category AS category, COUNT(*) AS count
        FROM complaints
        GROUP BY final_category
        ORDER BY final_category
        """
    )
    print("category distribution:")
    for row in cursor.fetchall():
        print(f"- {row['category']}: {row['count']}")

    cursor.execute(
        """
        SELECT status, COUNT(*) AS count
        FROM complaints
        GROUP BY status
        ORDER BY status
        """
    )
    print("status distribution:")
    for row in cursor.fetchall():
        print(f"- {row['status']}: {row['count']}")


def main() -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            admin_id = insert_admin(cursor)
            user_ids = insert_parents(cursor)
            insert_complaints(cursor, user_ids, admin_id)
            print_summary(cursor)
        conn.commit()

    print("demo complaints seeded")


if __name__ == "__main__":
    main()
