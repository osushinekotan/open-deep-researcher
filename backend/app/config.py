import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
DOCUMENT_METADATA_FILE = DOCUMENTS_DIR / "metadata" / "info.json"

DOCUMENT_METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


def get_research_fts_database(research_id: str) -> Path:
    """研究IDに基づいたFTSデータベースのパスを取得"""
    fts_db_dir = DATA_DIR / "fts_databases"
    fts_db_dir.mkdir(parents=True, exist_ok=True)
    return fts_db_dir / f"{research_id}.sqlite"
