import json
import shutil
from datetime import datetime

from fastapi import UploadFile

from app.config import DOCUMENT_METADATA_FILE, DOCUMENTS_DIR
from app.models.document import DocumentStatus


class DocumentManager:
    def __init__(self):
        self.documents_dir = DOCUMENTS_DIR
        self.metadata_file = DOCUMENT_METADATA_FILE

        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)

        # インデックス情報ファイルが存在しない場合は作成
        if not self.metadata_file.exists():
            with open(self.metadata_file, "w") as f:
                json.dump({"indexed_at": None, "enabled_files": []}, f)

    async def upload_documents(self, files: list[UploadFile], user_id: str | None = None) -> list[UploadFile]:
        """ドキュメントをアップロード"""
        uploaded_files = []

        for file in files:
            file_path = self.documents_dir / file.filename

            # ファイルを保存
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            uploaded_files.append(file)
            self._add_to_metadata(file.filename, user_id)

        return uploaded_files

    async def list_documents(self, user_id: str | None = None) -> list[DocumentStatus]:
        """アップロードされたドキュメントのリストを取得"""
        documents = []

        # インデックス情報の読み込み
        index_info = self._load_metadata()
        enabled_files = index_info.get("enabled_files", [])
        file_metadata = index_info.get("file_metadata", {})

        for file_path in self.documents_dir.glob("*.*"):
            if file_path.is_file() and file_path.name != "index_info.json":
                stat = file_path.stat()
                file_user_id = file_metadata.get(file_path.name, {}).get("user_id")
                # filter by user_id
                if user_id is not None and file_user_id != user_id:
                    continue

                documents.append(
                    DocumentStatus(
                        filename=file_path.name,
                        size=stat.st_size,
                        uploaded_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        is_enabled=file_path.name in enabled_files,
                        user_id=file_user_id,
                    )
                )

        return documents

    async def delete_document(self, filename: str) -> bool:
        """ドキュメントを削除"""
        file_path = self.documents_dir / filename
        if not file_path.is_file():
            return False

        file_path.unlink()
        self._remove_from_metadata(filename)

        return True

    async def set_document_enabled(self, filename: str, enable: bool) -> bool:
        """ドキュメントの使用可否を設定"""
        file_path = self.documents_dir / filename
        if not file_path.is_file():
            return False

        # インデックス情報を更新
        if enable:
            self._add_to_metadata(filename)
        else:
            self._remove_from_metadata(filename)

        return True

    def _load_metadata(self) -> dict:
        """インデックス情報を読み込む"""
        try:
            with open(self.metadata_file) as f:
                return json.load(f)
        except Exception:
            return {"enabled_files": []}

    def _save_metadata(self, metadata: dict):
        """インデックス情報を保存"""
        with open(self.metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

    def _add_to_metadata(self, filename: str, user_id: str | None = None):
        """インデックス情報にファイルを追加"""
        metadata = self._load_metadata()
        enabled_files = metadata.get("enabled_files", [])
        if filename not in enabled_files:
            enabled_files.append(filename)
            metadata["enabled_files"] = enabled_files

        # ファイルメタデータにユーザーIDを追加
        file_metadata = metadata.get("file_metadata", {})
        file_metadata[filename] = {"user_id": user_id}
        metadata["file_metadata"] = file_metadata

        self._save_metadata(metadata)

    def _remove_from_metadata(self, filename: str):
        """インデックス情報からファイルを削除"""
        metadata = self._load_metadata()
        enabled_files = metadata.get("enabled_files", [])
        if filename in enabled_files:
            enabled_files.remove(filename)
            metadata["enabled_files"] = enabled_files
            self._save_metadata(metadata)


_document_manager = None


def get_document_manager() -> DocumentManager:
    global _document_manager
    if _document_manager is None:
        _document_manager = DocumentManager()
    return _document_manager
