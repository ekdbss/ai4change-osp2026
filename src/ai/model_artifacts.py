from __future__ import annotations

import hashlib
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from src.config import get_env


MODEL_WEIGHT_FILES = ("model.safetensors", "pytorch_model.bin")
TOKENIZER_FILES = ("tokenizer_config.json", "spiece.model", "tokenizer.json")


def task_model_path(model_root: str | Path, task_name: str) -> Path:
    root = Path(model_root)
    task_path = root / task_name
    if task_path.exists():
        return task_path
    if task_name == "category":
        return root
    return task_path


def has_saved_model(model_path: str | Path) -> bool:
    path = Path(model_path)
    has_config = (path / "config.json").exists()
    has_weights = any((path / file_name).exists() for file_name in MODEL_WEIGHT_FILES)
    return has_config and has_weights


def model_file_size_mb(model_path: str | Path) -> float:
    path = Path(model_path)
    if not path.exists():
        return 0.0
    total_bytes = sum(file.stat().st_size for file in path.rglob("*") if file.is_file())
    return round(total_bytes / (1024 * 1024), 1)


def model_artifact_status(model_root: str | Path) -> dict:
    root = Path(model_root)
    category_path = task_model_path(root, "category")
    urgency_path = task_model_path(root, "urgency")
    category_ready = has_saved_model(category_path)
    urgency_ready = has_saved_model(urgency_path)

    return {
        "model_root": str(root),
        "category_path": str(category_path),
        "urgency_path": str(urgency_path),
        "category_ready": category_ready,
        "urgency_ready": urgency_ready,
        "model_ready": category_ready or urgency_ready,
        "category_size_mb": model_file_size_mb(category_path) if category_ready else 0.0,
        "urgency_size_mb": model_file_size_mb(urgency_path) if urgency_ready else 0.0,
    }


def ensure_model_artifacts(model_root: str | Path) -> dict:
    status = model_artifact_status(model_root)
    if status["model_ready"]:
        status["download_attempted"] = False
        status["download_error"] = ""
        return status

    model_url = get_env("KOBERT_MODEL_ZIP_URL")
    if not model_url:
        status["download_attempted"] = False
        status["download_error"] = "KOBERT_MODEL_ZIP_URL 값이 없어 모델 자동 설치를 건너뜁니다."
        return status

    try:
        _download_and_extract_model(model_url, Path(model_root))
        status = model_artifact_status(model_root)
        status["download_attempted"] = True
        status["download_error"] = ""
        return status
    except Exception as exc:
        status["download_attempted"] = True
        status["download_error"] = f"모델 자동 설치 실패: {exc}"
        return status


def _download_and_extract_model(model_url: str, model_root: Path) -> None:
    expected_sha256 = get_env("KOBERT_MODEL_ZIP_SHA256")
    download_token = get_env("KOBERT_MODEL_DOWNLOAD_TOKEN")

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        archive_path = temp_dir / "kobert_model.zip"
        extract_dir = temp_dir / "extract"

        request = urllib.request.Request(model_url)
        if download_token:
            request.add_header("Authorization", f"Bearer {download_token}")

        with urllib.request.urlopen(request, timeout=600) as response:
            with archive_path.open("wb") as output:
                shutil.copyfileobj(response, output)

        if expected_sha256:
            actual_sha256 = _sha256(archive_path)
            if actual_sha256.lower() != expected_sha256.lower():
                raise ValueError("다운로드한 모델 zip의 SHA256 값이 일치하지 않습니다.")

        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(extract_dir)

        source_model_dir = _find_saved_model_dir(extract_dir)
        if source_model_dir is None:
            raise FileNotFoundError("zip 안에서 model/saved_model 폴더를 찾지 못했습니다.")

        model_root.parent.mkdir(parents=True, exist_ok=True)
        if model_root.exists():
            shutil.rmtree(model_root)
        shutil.copytree(source_model_dir, model_root)


def _find_saved_model_dir(extract_dir: Path) -> Path | None:
    candidates = [
        extract_dir / "model" / "saved_model",
        extract_dir / "saved_model",
    ]
    candidates.extend(path for path in extract_dir.rglob("saved_model") if path.is_dir())

    for candidate in candidates:
        if has_saved_model(task_model_path(candidate, "category")) or has_saved_model(
            task_model_path(candidate, "urgency")
        ):
            return candidate
    return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
