from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
USERS_DIR = DATA_DIR / "users"


USERS_DIR.mkdir(parents=True, exist_ok=True)

# 匿名ユーザー用のディレクトリ名
ANONYMOUS_USER_DIR = "anonymous"


def get_user_documents_dir(username: str = None) -> Path:
    """ユーザー別ドキュメントディレクトリのパスを取得"""
    user_dir = username if username else ANONYMOUS_USER_DIR
    documents_dir = USERS_DIR / user_dir / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)
    return documents_dir


def get_document_metadata_file(username: str = None) -> Path:
    """ユーザー別ドキュメントメタデータファイルのパスを取得"""
    user_dir = username if username else ANONYMOUS_USER_DIR
    metadata_file = USERS_DIR / user_dir / "info.json"
    return metadata_file


def get_research_fts_database(research_id: str) -> Path:
    """研究IDに基づいたFTSデータベースのパスを取得"""
    fts_db_dir = DATA_DIR / "fts_databases"
    fts_db_dir.mkdir(parents=True, exist_ok=True)
    return fts_db_dir / f"{research_id}.sqlite"
