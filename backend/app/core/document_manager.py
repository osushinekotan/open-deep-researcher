import json
import shutil
from datetime import datetime

from fastapi import UploadFile

from app.config import DOCUMENTS_DIR, FTS_DATABASE
from app.models.document import DocumentStatus

INDEX_INFO_FILE = DOCUMENTS_DIR / "metadata" / "index_info.json"


class DocumentManager:
    def __init__(self):
        self.documents_dir = DOCUMENTS_DIR
        self.fts_database = FTS_DATABASE
        self.index_info_file = INDEX_INFO_FILE

        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.index_info_file.parent.mkdir(parents=True, exist_ok=True)

        # インデックス情報ファイルが存在しない場合は作成
        if not self.index_info_file.exists():
            with open(self.index_info_file, "w") as f:
                json.dump({"indexed_at": None, "enabled_files": []}, f)

    async def upload_documents(self, files: list[UploadFile]) -> list[UploadFile]:
        """ドキュメントをアップロード"""
        uploaded_files = []

        for file in files:
            file_path = self.documents_dir / file.filename

            # ファイルを保存
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            uploaded_files.append(file)

            # インデックス情報に追加（デフォルトで有効）
            self._add_to_index_info(file.filename)

        return uploaded_files

    async def list_documents(self) -> list[DocumentStatus]:
        """アップロードされたドキュメントのリストを取得"""
        documents = []

        # インデックス情報の読み込み
        index_info = self._load_index_info()
        enabled_files = index_info.get("enabled_files", [])

        for file_path in self.documents_dir.glob("*.*"):
            if file_path.is_file() and file_path.name != "index_info.json":
                # ファイル情報を取得
                stat = file_path.stat()

                documents.append(
                    DocumentStatus(
                        filename=file_path.name,
                        size=stat.st_size,
                        uploaded_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        is_enabled=file_path.name in enabled_files,
                    )
                )

        return documents

    async def delete_document(self, filename: str) -> bool:
        """ドキュメントを削除"""
        file_path = self.documents_dir / filename
        if not file_path.is_file():
            return False

        file_path.unlink()
        self._remove_from_index_info(filename)

        return True

    async def set_document_enabled(self, filename: str, enable: bool) -> bool:
        """ドキュメントの使用可否を設定"""
        file_path = self.documents_dir / filename
        if not file_path.is_file():
            return False

        # インデックス情報を更新
        if enable:
            self._add_to_index_info(filename)
        else:
            self._remove_from_index_info(filename)

        return True

    def _load_index_info(self) -> dict:
        """インデックス情報を読み込む"""
        try:
            with open(self.index_info_file) as f:
                return json.load(f)
        except Exception:
            return {"indexed_at": None, "enabled_files": []}

    def _save_index_info(self, index_info: dict):
        """インデックス情報を保存"""
        with open(self.index_info_file, "w") as f:
            json.dump(index_info, f, indent=2)

    def _add_to_index_info(self, filename: str):
        """インデックス情報にファイルを追加"""
        index_info = self._load_index_info()
        enabled_files = index_info.get("enabled_files", [])
        if filename not in enabled_files:
            enabled_files.append(filename)
            index_info["enabled_files"] = enabled_files
            self._save_index_info(index_info)

    def _remove_from_index_info(self, filename: str):
        """インデックス情報からファイルを削除"""
        index_info = self._load_index_info()
        enabled_files = index_info.get("enabled_files", [])
        if filename in enabled_files:
            enabled_files.remove(filename)
            index_info["enabled_files"] = enabled_files
            self._save_index_info(index_info)


_document_manager = None


def get_document_manager() -> DocumentManager:
    global _document_manager
    if _document_manager is None:
        _document_manager = DocumentManager()
    return _document_manager
