import json
import shutil
from datetime import datetime
from typing import Any

from fastapi import UploadFile

from app.config import DOCUMENTS_DIR, VECTOR_STORE_DIR
from app.models.document import CollectionCreate, CollectionResponse, DocumentStatus


class DocumentManager:
    def __init__(self):
        self.documents_dir = DOCUMENTS_DIR
        self.vector_store_dir = VECTOR_STORE_DIR
        self.collections_file = self.documents_dir / "collections.json"

        # コレクション情報ファイルが存在しない場合は作成
        if not self.collections_file.exists():
            with open(self.collections_file, "w") as f:
                json.dump([], f)

    async def upload_documents(self, files: list[UploadFile]) -> list[UploadFile]:
        """ドキュメントをアップロード"""
        uploaded_files = []

        for file in files:
            file_path = self.documents_dir / file.filename

            # ファイルを保存
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            uploaded_files.append(file)

        return uploaded_files

    async def list_documents(self) -> list[DocumentStatus]:
        """アップロードされたドキュメントのリストを取得"""
        documents = []

        for file_path in self.documents_dir.glob("*.*"):
            if file_path.is_file() and file_path.name != "collections.json":
                # ファイル情報を取得
                stat = file_path.stat()

                documents.append(
                    DocumentStatus(
                        filename=file_path.name,
                        size=stat.st_size,
                        uploaded_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        processed=self._is_document_processed(file_path.name),
                    )
                )

        return documents

    def _is_document_processed(self, filename: str) -> bool:
        """ドキュメントが処理済みかどうかを確認"""
        # ベクトルストアのメタデータファイルをチェック
        for metadata_file in self.vector_store_dir.glob("doc_metadata_*.json"):
            try:
                with open(metadata_file) as f:
                    metadata = json.load(f)
                    if filename in metadata:
                        return True
            except Exception:
                pass

        return False

    async def create_collection(self, collection: CollectionCreate) -> CollectionResponse:
        """新しいコレクションを作成"""
        # 既存のコレクションを読み込み
        collections = self._load_collections()

        # 同名のコレクションがないか確認
        for existing in collections:
            if existing["name"] == collection.name:
                # 既存のコレクションを更新
                existing["description"] = collection.description
                self._save_collections(collections)
                return CollectionResponse(
                    name=existing["name"],
                    description=existing["description"],
                    document_count=len(existing.get("documents", [])),
                )

        # 新しいコレクションを追加
        new_collection = {
            "name": collection.name,
            "description": collection.description,
            "created_at": datetime.now().isoformat(),
            "documents": [],
        }

        collections.append(new_collection)
        self._save_collections(collections)

        return CollectionResponse(
            name=new_collection["name"], description=new_collection["description"], document_count=0
        )

    async def list_collections(self) -> list[CollectionResponse]:
        """コレクションのリストを取得"""
        collections = self._load_collections()

        return [
            CollectionResponse(
                name=c["name"], description=c.get("description"), document_count=len(c.get("documents", []))
            )
            for c in collections
        ]

    async def delete_collection(self, name: str) -> bool:
        """コレクションを削除"""
        collections = self._load_collections()

        # コレクションを検索
        for i, collection in enumerate(collections):
            if collection["name"] == name:
                # コレクションを削除
                collections.pop(i)
                self._save_collections(collections)
                return True

        return False

    def _load_collections(self) -> list[dict[str, Any]]:
        """コレクション情報を読み込み"""
        try:
            with open(self.collections_file) as f:
                return json.load(f)
        except Exception:
            return []

    def _save_collections(self, collections: list[dict[str, Any]]):
        """コレクション情報を保存"""
        with open(self.collections_file, "w") as f:
            json.dump(collections, f, indent=2)

    async def add_document_to_collection(self, collection_name: str, filename: str) -> bool:
        """ドキュメントをコレクションに追加"""
        # ファイルの存在を確認
        file_path = self.documents_dir / filename
        if not file_path.exists():
            return False

        # コレクションを読み込み
        collections = self._load_collections()

        # コレクションを検索
        for collection in collections:
            if collection["name"] == collection_name:
                # 既に追加済みでないか確認
                if filename not in collection.get("documents", []):
                    if "documents" not in collection:
                        collection["documents"] = []
                    collection["documents"].append(filename)
                    self._save_collections(collections)
                return True

        return False

    async def get_collection_documents(self, collection_name: str) -> list[DocumentStatus]:
        """コレクション内のドキュメントリストを取得"""
        # コレクションを読み込み
        collections = self._load_collections()

        # コレクションを検索
        for collection in collections:
            if collection["name"] == collection_name:
                documents = []

                for filename in collection.get("documents", []):
                    file_path = self.documents_dir / filename
                    if file_path.exists():
                        # ファイル情報を取得
                        stat = file_path.stat()

                        documents.append(
                            DocumentStatus(
                                filename=filename,
                                size=stat.st_size,
                                uploaded_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                processed=self._is_document_processed(filename),
                            )
                        )

                return documents

        return []


_document_manager = None


def get_document_manager() -> DocumentManager:
    global _document_manager
    if _document_manager is None:
        _document_manager = DocumentManager()
    return _document_manager
