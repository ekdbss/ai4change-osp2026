import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


def _get_streamlit_secret(name: str) -> str | None:
    try:
        import streamlit as st

        value = st.secrets.get(name)
        if value is None:
            return None
        return str(value)
    except Exception:
        return None


def get_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name) or _get_streamlit_secret(name) or default


def get_model_path() -> str:
    return get_env("KOBERT_MODEL_PATH", str(ROOT_DIR / "model" / "saved_model"))


def get_base_model_name() -> str:
    return get_env("BASE_MODEL_NAME", "skt/kobert-base-v1")
