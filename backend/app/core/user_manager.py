import uuid
from datetime import datetime

from app.core.document_manager import get_document_manager
from app.core.research_manager import get_research_manager
from app.db.models import User, get_db_context


class UserManager:
    def __init__(self):
        self.document_manager = get_document_manager()
        self.research_manager = get_research_manager()

    async def create_user(self, username: str) -> dict | None:
        """新しいユーザーを作成"""
        try:
            user_id = str(uuid.uuid4())
            now = datetime.now().isoformat()

            with get_db_context() as db:
                # 同じユーザー名が既に存在するかチェック
                existing_user = db.query(User).filter(User.username == username).first()
                if existing_user:
                    return None

                # 新しいユーザーを作成
                new_user = User(
                    id=user_id,
                    username=username,
                    created_at=now,
                )
                db.add(new_user)
                db.commit()

                return {
                    "id": user_id,
                    "username": username,
                    "created_at": now,
                }
        except Exception as e:
            print(f"ユーザー作成中にエラーが発生しました: {e}")
            return None

    async def get_user(self, user_id: str) -> dict | None:
        """ユーザー情報を取得"""
        try:
            with get_db_context() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return None

                return {
                    "id": user.id,
                    "username": user.username,
                    "created_at": user.created_at,
                }
        except Exception as e:
            print(f"ユーザー情報取得中にエラーが発生しました: {e}")
            return None

    async def get_user_researches(self, user_id: str) -> list:
        """ユーザーのリサーチ一覧を取得"""
        return await self.research_manager.list_researches(user_id=user_id)

    async def get_user_documents(self, user_id: str) -> list:
        """ユーザーのドキュメント一覧を取得"""
        return await self.document_manager.list_documents(user_id=user_id)


_user_manager = None


def get_user_manager() -> UserManager:
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
    return _user_manager
