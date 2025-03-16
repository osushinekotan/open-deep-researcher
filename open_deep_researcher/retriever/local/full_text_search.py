import asyncio
import sqlite3
from pathlib import Path
from typing import Any

from langchain.schema import Document
from langchain_community.document_loaders import (
    CSVLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langsmith import traceable

from open_deep_researcher.utils import deduplicate_and_format_sources

LOADER_MAPPING = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
    ".csv": CSVLoader,
}


def get_loader_for_extension(file_path: str | Path) -> type:
    """ファイル拡張子に基づいて適切なローダークラスを返す"""
    ext = Path(file_path).suffix.lower()
    if ext not in LOADER_MAPPING:
        # 認識されない拡張子はテキストローダーをデフォルトとする
        return TextLoader
    return LOADER_MAPPING[ext]


async def load_document(file_path: str | Path) -> list[Document]:
    """拡張子に基づいて適切なローダーでドキュメントを読み込む"""
    path = Path(file_path)
    loader_class = get_loader_for_extension(path)

    try:
        loader = loader_class(str(path))  # Loaderは通常文字列パスを期待する
        loop = asyncio.get_event_loop()
        docs = await loop.run_in_executor(None, loader.load)
        return docs
    except Exception as e:
        print(f"エラー: {path}の読み込み中に問題が発生しました: {e}")
        return []


def chunk_documents(documents: list[Document], chunk_size: int = 1000, chunk_overlap: int = 200) -> list[Document]:
    """ドキュメントを指定されたサイズのチャンクに分割する

    Args:
        documents: 分割するドキュメントのリスト
        chunk_size: 各チャンクの最大サイズ（文字数）
        chunk_overlap: チャンク間のオーバーラップ（文字数）

    Returns:
        チャンクに分割されたドキュメントのリスト
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            "\n",
            " ",
            ".",
            ",",
            "\u200b",  # Zero-width space
            "\uff0c",  # Fullwidth comma
            "\u3001",  # Ideographic comma
            "\uff0e",  # Fullwidth full stop
            "\u3002",  # Ideographic full stop
            "",
        ],
    )

    return text_splitter.split_documents(documents)


class SQLiteFTSDocumentRetriever:
    """SQLite FTSを使用した全文検索レトリーバー"""

    def __init__(self, db_path: str):
        """initialize SQLiteFTSDocumentRetriever

        Args:
            db_path: SQLiteデータベースのパス
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """FTS検索を実行"""
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT
                file_path,
                title,
                content,
                chunk_id,
                highlight(documents_fts, 0, '<mark>', '</mark>') as title_highlight,
                highlight(documents_fts, 1, '<mark>', '</mark>') as content_highlight
            FROM documents_fts
            WHERE documents_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "file_path": row["file_path"],
                    "title": row["title"],
                    "content": row["content"],
                    "chunk_id": row["chunk_id"],
                    "title_highlight": row["title_highlight"],
                    "content_highlight": row["content_highlight"],
                }
            )

        return results

    def create_document_table(self):
        """ドキュメントデータ用のテーブルとFTSインデックスを作成"""
        cursor = self.conn.cursor()

        # ドキュメントテーブルを作成
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT,
            title TEXT,
            content TEXT,
            chunk_id TEXT
        )
        """)

        # FTSテーブルを作成
        cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
            title,
            content,
            file_path UNINDEXED,
            chunk_id UNINDEXED,
            content='documents',
            content_rowid='id',
            tokenize='trigram'
        )
        """)

        # FTSテーブル更新用のトリガーを作成
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
            INSERT INTO documents_fts(rowid, title, content, file_path, chunk_id)
            VALUES (new.id, new.title, new.content, new.file_path, new.chunk_id);
        END;
        """)

        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
            INSERT INTO documents_fts(documents_fts, rowid, title, content, file_path, chunk_id)
            VALUES('delete', old.id, old.title, old.content, old.file_path, old.chunk_id);
        END;
        """)

        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
            INSERT INTO documents_fts(documents_fts, rowid, title, content, file_path, chunk_id)
            VALUES('delete', old.id, old.title, old.content, old.file_path, old.chunk_id);
            INSERT INTO documents_fts(rowid, title, content, file_path, chunk_id)
            VALUES (new.id, new.title, new.content, new.file_path, new.chunk_id);
        END;
        """)

        self.conn.commit()

    def insert_documents(self, documents: list[dict[str, str]]):
        """ドキュメントデータをデータベースに挿入

        Args:
            documents: ドキュメントデータのリスト（各要素はファイルパス、タイトル、コンテンツ、チャンクIDを含む）
        """
        cursor = self.conn.cursor()

        for doc in documents:
            cursor.execute(
                """
                INSERT INTO documents (file_path, title, content, chunk_id)
                VALUES (?, ?, ?, ?)
                """,
                (
                    doc["file_path"],
                    doc["title"],
                    doc["content"],
                    doc["chunk_id"],
                ),
            )

        self.conn.commit()

    def get_db_stats(self) -> dict[str, Any]:
        """データベースの統計情報を取得

        Returns:
            統計情報を含む辞書
        """
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM documents")
        total_docs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT file_path) FROM documents")
        unique_files = cursor.fetchone()[0]

        return {"total_chunks": total_docs, "unique_files": unique_files}

    def close(self):
        """データベース接続を閉じる"""
        self.conn.close()


@traceable
async def initialize_knowledge_base(
    local_document_path: str | Path,
    db_path: str | Path,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    enabled_files: list[str] | None = None,
    **kwargs,
) -> Any | None:
    """指定されたディレクトリ内のドキュメントを処理してFTSデータベースを作成

    Args:
        local_document_path: ドキュメントが含まれるディレクトリ
        db_path: SQLiteデータベースを保存するパス（デフォルト: None、指定されない場合は一時ファイルを使用）
        chunk_size: 各チャンクの最大サイズ（文字数）
        chunk_overlap: チャンク間のオーバーラップ（文字数）
        enabled_files: 有効なファイル名のリスト（指定された場合はそのファイルのみ処理）

    Returns:
        データベースパスまたは処理に失敗した場合はNone
    """
    # Pathオブジェクトに変換
    doc_path = Path(local_document_path)
    db_path = Path(db_path)

    db_path.unlink(missing_ok=True)  # 常に新しく作成するため
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"データベースパス: {db_path}")
    print(f"チャンクサイズ: {chunk_size}, オーバーラップ: {chunk_overlap}")
    if enabled_files:
        print(f"有効なファイル数: {len(enabled_files)}")

    try:
        # レトリーバーを初期化
        retriever = SQLiteFTSDocumentRetriever(str(db_path))
        retriever.create_document_table()

        # ディレクトリ内のすべてのドキュメントを収集
        all_files = []
        for file_path in doc_path.glob("*"):  # sub directories are not included
            if file_path.is_file() and file_path.suffix.lower() in LOADER_MAPPING:
                # 有効なファイルリストが指定されている場合、そのリストにあるファイルのみを処理
                if enabled_files is None or file_path.name in enabled_files:
                    all_files.append(file_path)

        if not all_files:
            print("読み込み可能なドキュメントが見つかりません。")
            return None

        # 各ファイルを処理
        documents_to_insert = []
        total_chunks = 0

        for file_path in all_files:
            rel_path = str(file_path.relative_to(doc_path))
            print(f"ドキュメントを処理中: {rel_path}")

            # ドキュメントを読み込む
            docs = await load_document(file_path)
            chunked_docs = chunk_documents(docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

            for i, chunk in enumerate(chunked_docs):
                chunk_id = f"{rel_path}_{i}"

                # ドキュメントデータを作成
                doc_data = {
                    "file_path": rel_path,
                    "title": f"{file_path.name} (chunk {i + 1}/{len(chunked_docs)})",
                    "content": chunk.page_content,
                    "chunk_id": chunk_id,
                }
                documents_to_insert.append(doc_data)
                total_chunks += 1

        # ドキュメントをデータベースに挿入
        if documents_to_insert:
            retriever.insert_documents(documents_to_insert)
            print(f"{len(all_files)}個のファイルから{total_chunks}個のチャンクを処理しました。")

        retriever.close()
        return str(db_path)

    except Exception as e:
        print(f"ドキュメント処理中にエラーが発生しました: {e}")
        import traceback

        print(traceback.format_exc())
        return None


@traceable
async def search_local_documents(
    query: str,
    db_path: str | Path,
    top_k: int = 5,
    **kwargs,
):
    """SQLite FTSを使用してローカルドキュメントを検索

    Args:
        query: 検索クエリ
        db_path: SQLiteデータベースへのパス
        top_k: 返す結果の数（デフォルト: 5）

    Returns:
        検索結果のリスト
    """
    try:
        retriever = SQLiteFTSDocumentRetriever(str(db_path))
        results = retriever.search(query, limit=top_k)

        formatted_results = []
        for doc in results:
            # 見つかったチャンク情報を含める
            chunk_info = f" (チャンクID: {doc['chunk_id']})" if "chunk_id" in doc else ""

            formatted_results.append(
                {
                    "title": f"{doc['title']}{chunk_info}",
                    "url": doc["file_path"],  # ファイルパスをURLとして使用
                    "content": doc["content_highlight"] if "content_highlight" in doc else doc["content"],
                    "score": 1.0,  # FTSはスコアを返さないため固定値
                    "raw_content": doc["content"],
                }
            )

        retriever.close()
        return [
            {
                "query": query,
                "follow_up_questions": None,
                "answer": None,
                "images": [],
                "results": formatted_results,
            }
        ]
    except Exception as e:
        print(f"ローカルドキュメント検索中にエラーが発生しました: {e}")
        return [
            {
                "query": query,
                "follow_up_questions": None,
                "answer": None,
                "images": [],
                "results": [],
                "error": str(e),
            }
        ]


@traceable
async def local_search(
    query_list: list[str],
    db_path: str | Path | None = None,
    top_k: int = 5,
    max_tokens_per_source: int = 8192,
    **kwargs,
) -> str:
    """SQLite FTSを使用してローカルドキュメントを検索

    Args:
        query_list: 検索クエリのリスト
        db_path: SQLiteデータベースへのパス
        top_k: 返す上位結果の数（デフォルト: 5）
        max_tokens_per_source: ソースあたりの最大トークン数

    Returns:
        検索結果の文字列
    """
    search_docs = []
    for query in query_list:
        try:
            result = await search_local_documents(
                query,
                db_path,
                top_k=top_k,
            )
            search_docs.extend(result)
        except Exception as e:
            print(f"クエリ '{query}'のローカル検索中にエラーが発生しました: {str(e)}")
            search_docs.append(
                {
                    "query": query,
                    "follow_up_questions": None,
                    "answer": None,
                    "images": [],
                    "results": [],
                    "error": str(e),
                }
            )
    print(search_docs)
    return deduplicate_and_format_sources(search_docs, max_tokens_per_source=max_tokens_per_source)
