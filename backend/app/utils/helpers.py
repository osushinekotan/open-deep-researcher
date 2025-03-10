import json
import os
from pathlib import Path
from typing import Any


def ensure_directories(*dirs):
    """ディレクトリが存在することを確認し、存在しない場合は作成"""
    for directory in dirs:
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)


def save_json(data: dict[str, Any], file_path: str):
    """データをJSON形式で保存"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(file_path: str) -> dict[str, Any]:
    """JSON形式のデータを読み込み"""
    if not os.path.exists(file_path):
        return {}

    with open(file_path, encoding="utf-8") as f:
        return json.load(f)
