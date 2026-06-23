from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_DIR = ROOT_DIR / "model" / "saved_model"
DEFAULT_REPORT_DIR = ROOT_DIR / "reports"


def copy_tree(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def main() -> None:
    parser = argparse.ArgumentParser(description="Install KoBERT artifacts exported from Colab.")
    parser.add_argument("zip_path", type=Path, help="Path to kobert_v1_1800.zip")
    parser.add_argument("--keep-temp", action="store_true")
    args = parser.parse_args()

    zip_path = args.zip_path.resolve()
    if not zip_path.exists():
        raise FileNotFoundError(f"zip 파일을 찾을 수 없습니다: {zip_path}")

    temp_dir = ROOT_DIR / ".tmp_colab_model"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)

    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(temp_dir)

    source_model_dir = temp_dir / "model" / "saved_model"
    source_report_dir = temp_dir / "reports"

    if not source_model_dir.exists():
        raise FileNotFoundError("zip 안에서 model/saved_model 폴더를 찾지 못했습니다.")

    copy_tree(source_model_dir, DEFAULT_MODEL_DIR)
    if source_report_dir.exists():
        copy_tree(source_report_dir, DEFAULT_REPORT_DIR)

    if not args.keep_temp:
        shutil.rmtree(temp_dir)

    print(f"installed model: {DEFAULT_MODEL_DIR}")
    if DEFAULT_REPORT_DIR.exists():
        print(f"installed reports: {DEFAULT_REPORT_DIR}")


if __name__ == "__main__":
    main()
