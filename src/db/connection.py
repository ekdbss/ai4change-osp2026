from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

import pymysql
from dotenv import load_dotenv
from pymysql.connections import Connection

from src.config import get_env


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def is_db_configured() -> bool:
    required = ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"]
    return all(get_env(name) for name in required)


def get_connection() -> Connection:
    ssl_options = _build_ssl_options()
    connection_args = {
        "host": get_env("DB_HOST", "localhost"),
        "port": int(get_env("DB_PORT", "3306") or "3306"),
        "user": get_env("DB_USER", "root"),
        "password": get_env("DB_PASSWORD", ""),
        "database": get_env("DB_NAME", "school_complaints"),
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": False,
    }
    if ssl_options is not None:
        connection_args["ssl"] = ssl_options

    return pymysql.connect(**connection_args)


def _build_ssl_options() -> dict | None:
    mode = (get_env("DB_SSL_MODE", "") or "").upper()
    host = get_env("DB_HOST", "") or ""
    ca_path = get_env("DB_SSL_CA_PATH")
    ca_content = get_env("DB_SSL_CA")

    if mode in {"DISABLED", "FALSE", "NO", "0"}:
        return None

    if ca_content:
        ca_path = _write_ca_certificate(ca_content)

    if ca_path:
        return {
            "ca": ca_path,
            "check_hostname": mode == "VERIFY_IDENTITY",
            "verify_mode": "required",
        }

    if mode in {"REQUIRED", "VERIFY_CA", "VERIFY_IDENTITY"} or host.endswith(".aivencloud.com"):
        return {
            "check_hostname": False,
            "verify_mode": "none",
        }

    return None


def _write_ca_certificate(ca_content: str) -> str:
    normalized = ca_content.replace("\\n", "\n").strip() + "\n"
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    ca_path = Path(tempfile.gettempdir()) / f"scc_osp2026_db_ca_{digest}.pem"
    if not ca_path.exists():
        ca_path.write_text(normalized, encoding="utf-8")
    return str(ca_path)
