from __future__ import annotations

import hashlib
import os

import streamlit as st

from src.db.connection import get_connection, is_db_configured


ACTIVE_ROLE_KEY = "active_role"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_current_parent() -> dict | None:
    _normalize_single_role()
    if st.session_state.get(ACTIVE_ROLE_KEY) != "parent":
        return None
    return st.session_state.get("parent_user")


def get_current_admin() -> dict | None:
    _normalize_single_role()
    if st.session_state.get(ACTIVE_ROLE_KEY) != "admin":
        return None
    return st.session_state.get("admin_user")


def is_parent_logged_in() -> bool:
    return get_current_parent() is not None


def is_admin_logged_in() -> bool:
    return get_current_admin() is not None


def login_parent(parent_name: str, phone_tail: str) -> None:
    _clear_admin_state()
    st.session_state["parent_user"] = {
        "parent_name": parent_name.strip(),
        "phone_tail": phone_tail.strip(),
    }
    st.session_state[ACTIVE_ROLE_KEY] = "parent"


def logout_parent() -> None:
    _clear_parent_state()
    if st.session_state.get(ACTIVE_ROLE_KEY) == "parent":
        st.session_state.pop(ACTIVE_ROLE_KEY, None)


def login_admin(username: str, password: str) -> bool:
    admin_user = _verify_admin_from_db(username, password) or _verify_admin_from_env(
        username,
        password,
    )
    if not admin_user:
        return False

    _clear_parent_state()
    st.session_state["admin_user"] = admin_user
    st.session_state[ACTIVE_ROLE_KEY] = "admin"
    return True


def logout_admin() -> None:
    _clear_admin_state()
    if st.session_state.get(ACTIVE_ROLE_KEY) == "admin":
        st.session_state.pop(ACTIVE_ROLE_KEY, None)


def require_parent_login() -> dict:
    _normalize_single_role(preferred_role="parent")
    if st.session_state.get(ACTIVE_ROLE_KEY) == "admin":
        _render_role_switch_notice(
            current_role_label="관리자",
            target_role_label="학부모",
            logout_handler=logout_admin,
        )

    parent_user = get_current_parent()
    if parent_user:
        with st.sidebar:
            st.caption(f"학부모: {parent_user['parent_name']}")
            if st.button("학부모 로그아웃", use_container_width=True):
                logout_parent()
                st.rerun()
        return parent_user

    st.title("학부모 로그인")
    st.caption("민원 접수와 처리 현황 조회를 위해 간단한 본인 확인 정보를 입력합니다.")

    with st.form("parent_login_form"):
        parent_name = st.text_input("학부모 이름", placeholder="예: 김하윤")
        phone_tail = st.text_input("전화번호 뒤 4자리", max_chars=4, placeholder="예: 1234")
        submitted = st.form_submit_button("학부모로 시작하기", type="primary", use_container_width=True)

    if submitted:
        if not parent_name.strip():
            st.warning("학부모 이름을 입력해주세요.")
        elif not phone_tail.strip().isdigit() or len(phone_tail.strip()) != 4:
            st.warning("전화번호 뒤 4자리를 숫자로 입력해주세요.")
        else:
            login_parent(parent_name, phone_tail)
            st.rerun()

    st.stop()


def require_admin_login() -> dict:
    _normalize_single_role(preferred_role="admin")
    if st.session_state.get(ACTIVE_ROLE_KEY) == "parent":
        _render_role_switch_notice(
            current_role_label="학부모",
            target_role_label="관리자",
            logout_handler=logout_parent,
        )

    admin_user = get_current_admin()
    if admin_user:
        with st.sidebar:
            st.caption(f"관리자: {admin_user.get('display_name') or admin_user['username']}")
            st.caption(f"권한: {admin_user.get('role', 'teacher')}")
            if st.button("관리자 로그아웃", use_container_width=True):
                logout_admin()
                st.rerun()
        return admin_user

    st.title("관리자 로그인")
    st.caption("접수된 민원은 학교 관리자 계정으로 로그인한 뒤 확인할 수 있습니다.")

    with st.form("admin_login_form"):
        username = st.text_input("아이디", placeholder="admin")
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("관리자로 로그인", type="primary", use_container_width=True)

    if submitted:
        if login_admin(username.strip(), password):
            st.rerun()
        else:
            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

    st.info("데모 기본 계정은 admin / admin1234 입니다. 발표 전에는 .env에서 변경하세요.")
    st.stop()


def _normalize_single_role(preferred_role: str | None = None) -> None:
    active_role = st.session_state.get(ACTIVE_ROLE_KEY)
    has_parent = "parent_user" in st.session_state
    has_admin = "admin_user" in st.session_state

    if active_role == "parent":
        _clear_admin_state()
        if not has_parent:
            st.session_state.pop(ACTIVE_ROLE_KEY, None)
        return

    if active_role == "admin":
        _clear_parent_state()
        if not has_admin:
            st.session_state.pop(ACTIVE_ROLE_KEY, None)
        return

    if has_parent and has_admin:
        if preferred_role == "admin":
            _clear_parent_state()
            st.session_state[ACTIVE_ROLE_KEY] = "admin"
        else:
            _clear_admin_state()
            st.session_state[ACTIVE_ROLE_KEY] = "parent"
        return

    if has_parent:
        st.session_state[ACTIVE_ROLE_KEY] = "parent"
    elif has_admin:
        st.session_state[ACTIVE_ROLE_KEY] = "admin"
    else:
        st.session_state.pop(ACTIVE_ROLE_KEY, None)


def _clear_parent_state() -> None:
    st.session_state.pop("parent_user", None)
    st.session_state.pop("pending_complaint", None)
    st.session_state.pop("pending_attachments", None)


def _clear_admin_state() -> None:
    st.session_state.pop("admin_user", None)


def _render_role_switch_notice(
    current_role_label: str,
    target_role_label: str,
    logout_handler,
) -> None:
    st.title(f"{target_role_label} 로그인")
    st.warning(
        f"현재 {current_role_label} 계정으로 로그인되어 있습니다. "
        f"{target_role_label}로 이용하려면 먼저 로그아웃해주세요."
    )
    if st.button(
        f"{current_role_label} 로그아웃하고 {target_role_label} 로그인하기",
        type="primary",
        use_container_width=True,
    ):
        logout_handler()
        st.rerun()
    st.stop()


def _verify_admin_from_db(username: str, password: str) -> dict | None:
    if not username or not password or not is_db_configured():
        return None

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, username, password_hash, display_name, role
                    FROM admins
                    WHERE username = %s
                    LIMIT 1
                    """,
                    (username,),
                )
                row = cursor.fetchone()
    except Exception:
        return None

    if not row:
        return None

    if str(row.get("password_hash", "")).lower() != hash_password(password):
        return None

    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row.get("display_name") or row["username"],
        "role": row.get("role", "teacher"),
        "source": "db",
    }


def _verify_admin_from_env(username: str, password: str) -> dict | None:
    expected_username = os.getenv("ADMIN_USERNAME", "admin")
    expected_password = os.getenv("ADMIN_PASSWORD", "admin1234")

    if username != expected_username or password != expected_password:
        return None

    return {
        "id": None,
        "username": username,
        "display_name": "데모 관리자",
        "role": "admin",
        "source": "env",
    }
