from __future__ import annotations

import os
from pathlib import Path

import pymysql
from dotenv import load_dotenv
from pymysql.connections import Connection


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def is_db_configured() -> bool:
    required = ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"]
    return all(os.getenv(name) for name in required)


def get_connection() -> Connection:
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "school_complaints"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
