import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any

from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    CSVLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langsmith import traceable

from open_deep_researcher.retriever.utils import deduplicate_and_format_sources

LOADER_MAPPING = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
    ".csv": CSVLoader,
}


def compute_file_hash(file_path: str | Path) -> str:
    """ファイルのMD5ハッシュを計算して変更を追跡する"""
    path = Path(file_path)
    hasher = hashlib.md5()
    with path.open("rb") as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()


def hash_collection_name(path: str | Path) -> str:
    """
    パス文字列からハッシュベースのコレクション名を生成する

    Args:
        path: ハッシュするパス

    Returns:
        str: ハッシュベースのコレクション名
    """
    path_str = str(Path(path).absolute())
    hasher = hashlib.md5()
    hasher.update(path_str.encode("utf-8"))
    return "col_" + hasher.hexdigest()[:16]


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


def initialize_embeddings(embedding_provider: str, embedding_model: str) -> Any:
    """指定されたプロバイダーとモデルで埋め込みを初期化する"""
    if embedding_provider == "openai":
        return OpenAIEmbeddings(model=embedding_model)
    else:
        raise ValueError(f"サポートされていない埋め込みプロバイダー: {embedding_provider}")


@traceable
async def process_documents(  # noqa: C901
    local_document_path: str | Path,
    vector_store_path: str | Path,
    embedding_provider: str = "openai",
    embedding_model: str = "text-embedding-3-small",
    collection_name: str | None = None,
    **kwargs,
) -> Any | None:
    """指定されたディレクトリ内のドキュメントを処理して埋め込みを作成

    Args:
        local_document_path: ドキュメントが含まれるディレクトリ
        vector_store_path: ベクトルデータベースを保存するパス
        embedding_provider: 埋め込みのプロバイダー（デフォルト: openai）
        embedding_model: 埋め込みに使用するモデル（デフォルト: text-embedding-3-small）
        collection_name: ベクトルストアのコレクション名（デフォルト: Noneでローカルパスからハッシュ生成）

    Returns:
        ベクトルストアインスタンスまたは処理に失敗した場合はNone
    """
    # Pathオブジェクトに変換
    doc_path = Path(local_document_path)
    store_path = Path(vector_store_path)

    # ベクトルストアディレクトリが存在しない場合は作成
    store_path.mkdir(parents=True, exist_ok=True)

    # コレクション名が指定されていない場合は、local_document_pathからハッシュを生成
    if collection_name is None:
        collection_name = hash_collection_name(doc_path)

    print(f"Using collection name: {collection_name}")

    # メタデータファイル名にコレクション名を含める
    metadata_path = store_path / f"doc_metadata_{collection_name}.json"
    if metadata_path.exists():
        with metadata_path.open() as f:
            doc_metadata = json.load(f)
    else:
        doc_metadata = {}

    # ディレクトリ内のすべてのドキュメントを収集
    all_files = []
    for file_path in doc_path.glob("**/*"):
        if file_path.is_file() and file_path.suffix.lower() in LOADER_MAPPING:
            all_files.append(file_path)

    # 新規または変更されたファイルを特定
    new_files = []
    changed_files = []
    for file_path in all_files:
        file_hash = compute_file_hash(file_path)
        rel_path = str(file_path.relative_to(doc_path))

        if rel_path not in doc_metadata:
            # 新規ファイル
            new_files.append(file_path)
            doc_metadata[rel_path] = file_hash
        elif doc_metadata[rel_path] != file_hash:
            # 変更されたファイル
            changed_files.append(file_path)
            doc_metadata[rel_path] = file_hash

    # 処理が必要なファイルを結合
    files_to_process = new_files + changed_files

    if not files_to_process:
        print("新規または変更されたドキュメントはありません。")

        # 既存のベクトルストアがある場合はロード
        if store_path.exists():
            try:
                embeddings = initialize_embeddings(embedding_provider, embedding_model)
                vector_store = Chroma(
                    persist_directory=str(store_path), embedding_function=embeddings, collection_name=collection_name
                )
                return vector_store
            except Exception as e:
                print(f"ベクトルストアの読み込みエラー: {e}")
                return None
        else:
            print("既存のベクトルストアが見つかりません。")
            return None

    # 埋め込みを初期化
    try:
        embeddings = initialize_embeddings(embedding_provider, embedding_model)

        # ベクトルストアを初期化
        try:
            vector_store = Chroma(
                persist_directory=str(store_path), embedding_function=embeddings, collection_name=collection_name
            )
        except Exception:
            # コレクションが存在しない場合は新規作成 (空のドキュメントリストで初期化)
            vector_store = Chroma.from_documents(
                documents=[], embedding=embeddings, persist_directory=str(store_path), collection_name=collection_name
            )

        # 変更されたファイルの既存のベクトルを削除
        for file_path in changed_files:
            rel_path = str(file_path.relative_to(doc_path))
            print(f"変更されたドキュメントの既存ベクトルを削除中: {rel_path}")
            try:
                # source メタデータフィールドに基づいて削除
                vector_store.delete(where={"source": rel_path})
            except Exception as e:
                print(f"ベクトル削除中にエラーが発生しました: {e}")

        # 各ファイルを処理
        for file_path in files_to_process:
            rel_path = str(file_path.relative_to(doc_path))
            file_type = "新規" if file_path in new_files else "変更"
            print(f"{file_type}ドキュメントを処理中: {rel_path}")

            docs = await load_document(file_path)
            # メタデータにソース情報を追加
            for doc in docs:
                doc.metadata["source"] = rel_path

            # ドキュメントを適切なサイズに分割
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=4000,
                chunk_overlap=200,
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
            split_docs = text_splitter.split_documents(docs)

            # 分割したドキュメントをベクトルストアに追加
            if split_docs:
                vector_store.add_documents(split_docs)

        # メタデータを更新して永続化
        with metadata_path.open("w") as f:
            json.dump(doc_metadata, f)

        return vector_store

    except Exception as e:
        print(f"ドキュメント処理中にエラーが発生しました: {e}")
        import traceback

        print(traceback.format_exc())
        return None


def detect_collection_name(vector_store_path: str | Path) -> str | None:
    """
    ベクトルストアパスからコレクション名を検出する

    Args:
        vector_store_path: ベクトルストアのパス

    Returns:
        Optional[str]: 検出されたコレクション名、見つからない場合はNone
    """
    store_path = Path(vector_store_path)
    if not store_path.exists():
        return None

    # メタデータファイルパターンを基にコレクション名を探す
    metadata_files = list(store_path.glob("doc_metadata_*.json"))
    if metadata_files:
        # 最初に見つかったメタデータファイルからコレクション名を抽出
        filename = metadata_files[0].name
        return filename[len("doc_metadata_") : -len(".json")]

    return None


@traceable
async def search_local_documents(
    query: str,
    vector_store_path: str | Path,
    embedding_provider: str = "openai",
    embedding_model: str = "text-embedding-3-small",
    top_k: int = 5,
    collection_name: str | None = None,
):
    """ベクトルストアを使用してローカルドキュメントを検索

    Args:
        query: 検索クエリ
        vector_store_path: ベクトルストアへのパス
        embedding_provider: 埋め込みプロバイダー（デフォルト: openai）
        embedding_model: 埋め込みに使用するモデル（デフォルト: text-embedding-3-small）
        top_k: 返す結果の数（デフォルト: 5）
        collection_name: ベクトルストアのコレクション名（デフォルト: None）

    Returns:
        deduplicate_and_format_sources で使用するための検索結果のリスト
    """
    try:
        store_path = Path(vector_store_path)
        embeddings = initialize_embeddings(embedding_provider, embedding_model)
        vector_store = Chroma(
            persist_directory=str(store_path),
            embedding_function=embeddings,
            collection_name=collection_name,
        )

        results = vector_store.similarity_search_with_relevance_scores(query, k=top_k)
        formatted_results = []
        for doc, score in results:
            source = doc.metadata.get("source", "不明")
            formatted_results.append(
                {
                    "title": Path(source).name,
                    "url": source,
                    "content": doc.page_content,
                    "score": score,
                    "raw_content": "",
                }
            )

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
    search_queries: list[str],
    vector_store_path: str | Path,
    embedding_provider: str = "openai",
    embedding_model: str = "text-embedding-3-small",
    top_k: int = 5,
    collection_name: str | None = None,
    **kwargs,
) -> str:
    """ベクトル類似性を使用してローカルドキュメントを検索

    Args:
        search_queries: 検索クエリのリスト
        vector_store_path: ベクトルストアへのパス
        embedding_provider: 埋め込みプロバイダー（デフォルト: "openai"）
        embedding_model: 埋め込みモデル名（デフォルト: "text-embedding-3-small"）
        top_k: 返す上位結果の数（デフォルト: 5）
        collection_name: ベクトルストアのコレクション名（デフォルト: None）

    Returns:
        検索結果の文字列
    """

    if collection_name is None:
        collection_name = detect_collection_name(vector_store_path)
        if collection_name:
            print(f"Auto-detected collection name: {collection_name}")
        else:
            # 検出できなかった場合はデフォルト値を使用
            collection_name = "default"
            print(f"No collection name specified or detected, using default: {collection_name}")

    search_docs = []
    for query in search_queries:
        try:
            result = await search_local_documents(
                query,
                vector_store_path,
                embedding_provider,
                embedding_model,
                top_k,
                collection_name,
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

    return deduplicate_and_format_sources(search_docs, max_tokens_per_source=8000)
