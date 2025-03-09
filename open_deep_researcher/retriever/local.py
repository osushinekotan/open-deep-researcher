import asyncio
import hashlib
import json
import os
from typing import Any

from langchain.schema import Document
from langchain_community.document_loaders import (
    CSVLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredExcelLoader,
    UnstructuredMarkdownLoader,
)
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langsmith import traceable

from open_deep_researcher.retriever.utils import deduplicate_and_format_sources

LOADER_MAPPING = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
    ".md": UnstructuredMarkdownLoader,
    ".csv": CSVLoader,
    ".xls": UnstructuredExcelLoader,
    ".xlsx": UnstructuredExcelLoader,
}


def compute_file_hash(file_path: str) -> str:
    """ファイルのMD5ハッシュを計算して変更を追跡する"""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()


async def load_document(file_path: str) -> list[Document]:
    """拡張子に基づいて適切なローダーでドキュメントを読み込む"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in LOADER_MAPPING:
        # 認識されない拡張子はテキストローダーをデフォルトとする
        loader_class = TextLoader
    else:
        loader_class = LOADER_MAPPING[ext]

    try:
        loader = loader_class(file_path)
        # ブロッキングを避けるためにエグゼキュータで実行
        loop = asyncio.get_event_loop()
        docs = await loop.run_in_executor(None, loader.load)
        return docs
    except Exception as e:
        print(f"エラー: {file_path}の読み込み中に問題が発生しました: {e}")
        return []


@traceable
async def process_documents(  # noqa: C901
    doc_dir: str,
    vector_store_path: str,
    embedding_provider: str = "openai",
    embedding_model: str = "text-embedding-3-small",
) -> Any | None:
    """指定されたディレクトリ内のドキュメントを処理して埋め込みを作成

    Args:
        doc_dir: ドキュメントが含まれるディレクトリ
        vector_store_path: ベクトルデータベースを保存するパス
        embedding_provider: 埋め込みのプロバイダー（デフォルト: openai）
        embedding_model: 埋め込みに使用するモデル（デフォルト: text-embedding-3-small）

    Returns:
        ベクトルストアインスタンスまたは処理に失敗した場合はNone
    """
    # ベクトルストアディレクトリが存在しない場合は作成
    os.makedirs(vector_store_path, exist_ok=True)
    metadata_path = os.path.join(vector_store_path, "doc_metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path) as f:
            doc_metadata = json.load(f)
    else:
        doc_metadata = {}

    # ディレクトリ内のすべてのドキュメントを収集
    all_files = []
    for root, _, files in os.walk(doc_dir):
        for file in files:
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()
            if ext in LOADER_MAPPING:
                all_files.append(file_path)

    # 新規または変更されたファイルを特定
    new_files = []
    for file_path in all_files:
        file_hash = compute_file_hash(file_path)
        rel_path = os.path.relpath(file_path, doc_dir)

        if rel_path not in doc_metadata or doc_metadata[rel_path] != file_hash:
            new_files.append(file_path)
            doc_metadata[rel_path] = file_hash

    if not new_files:
        print("新規または変更されたドキュメントはありません。")

        # 既存のベクトルストアがある場合はロード
        if os.path.exists(vector_store_path) and os.listdir(vector_store_path):
            try:
                if embedding_provider == "openai":
                    embeddings = OpenAIEmbeddings(model=embedding_model)
                else:
                    raise ValueError(f"サポートされていない埋め込みプロバイダー: {embedding_provider}")

                vector_store = Chroma(persist_directory=vector_store_path, embedding_function=embeddings)
                return vector_store
            except Exception as e:
                print(f"ベクトルストアの読み込みエラー: {e}")
                return None
        else:
            print("既存のベクトルストアが見つかりません。")
            return None

    # 埋め込みを初期化
    try:
        if embedding_provider == "openai":
            embeddings = OpenAIEmbeddings(model=embedding_model)
        else:
            raise ValueError(f"サポートされていない埋め込みプロバイダー: {embedding_provider}")

        all_docs = []
        for file_path in new_files:
            rel_path = os.path.relpath(file_path, doc_dir)
            print(f"ドキュメントを処理中: {rel_path}")
            docs = await load_document(file_path)

            for doc in docs:
                doc.metadata["source"] = rel_path

            all_docs.extend(docs)

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        split_docs = text_splitter.split_documents(all_docs)

        if os.path.exists(vector_store_path) and os.path.exists(os.path.join(vector_store_path, "chroma.sqlite3")):
            vector_store = Chroma(persist_directory=vector_store_path, embedding_function=embeddings)
            vector_store.add_documents(split_docs)
        else:
            vector_store = Chroma.from_documents(split_docs, embeddings, persist_directory=vector_store_path)

        with open(metadata_path, "w") as f:
            json.dump(doc_metadata, f)

        vector_store.persist()
        return vector_store

    except Exception as e:
        print(f"ドキュメント処理中にエラーが発生しました: {e}")
        return None


@traceable
async def search_local_documents(
    query: str,
    vector_store_path: str,
    embedding_provider: str = "openai",
    embedding_model: str = "text-embedding-3-small",
    top_k: int = 5,
):
    """ベクトルストアを使用してローカルドキュメントを検索

    Args:
        query: 検索クエリ
        vector_store_path: ベクトルストアへのパス
        embedding_provider: 埋め込みプロバイダー（デフォルト: openai）
        embedding_model: 埋め込みに使用するモデル（デフォルト: text-embedding-3-small）
        top_k: 返す結果の数（デフォルト: 5）

    Returns:
        deduplicate_and_format_sources で使用するための検索結果のリスト
    """
    try:
        # 埋め込みを初期化
        if embedding_provider == "openai":
            embeddings = OpenAIEmbeddings(model=embedding_model)
        else:
            raise ValueError(f"サポートされていない埋め込みプロバイダー: {embedding_provider}")

        vector_store = Chroma(persist_directory=vector_store_path, embedding_function=embeddings)
        results = vector_store.similarity_search_with_relevance_scores(query, k=top_k)
        formatted_results = []
        for doc, score in results:
            formatted_results.append(
                {
                    "title": os.path.basename(doc.metadata.get("source", "不明")),
                    "url": f"file://{doc.metadata.get('source', '')}",
                    "content": doc.page_content,
                    "score": score,
                    "raw_content": None,
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
    search_queries,
    vector_store_path: str,
    embedding_provider: str = "openai",
    embedding_model: str = "text-embedding-3-small",
    top_k: int = 5,
    **kwargs,
):
    """ベクトル類似性を使用してローカルドキュメントを検索

    Args:
        search_queries: 検索クエリのリスト
        vector_store_path: ベクトルストアへのパス
        embedding_provider: 埋め込みプロバイダー（デフォルト: "openai"）
        embedding_model: 埋め込みモデル名（デフォルト: "text-embedding-3-small"）
        top_k: 返す上位結果の数（デフォルト: 5）

    Returns:
        検索結果のリスト
    """
    search_docs = []
    for query in search_queries:
        try:
            result = await search_local_documents(
                query,
                vector_store_path,
                embedding_provider,
                embedding_model,
                top_k,
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

    return deduplicate_and_format_sources(search_docs, max_tokens_per_source=4000)
