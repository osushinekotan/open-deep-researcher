import sqlite3
from pathlib import Path
from typing import Any

from google.cloud import bigquery
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable
from pydantic import BaseModel, Field

from open_deep_researcher.utils import deduplicate_and_format_sources, expand_query


class SQLiteFTSPatentetriever:
    """SQLite FTSを使用した全文検索レトリーバー"""

    def __init__(self, db_path: str):
        """initialize SQLiteFTSRetriever

        Args:
            db_path: SQLiteデータベースのパス
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """FTS検索を実行

        Args:
            query: 検索クエリ
            limit: 取得する結果の最大数

        Returns:
            検索結果のリスト
        """
        cursor = self.conn.cursor()

        # FTS検索を実行
        cursor.execute(
            """
            SELECT
                patent_id,
                title,
                abstract,
                publication_date,
                url,
                highlight(patents_fts, 0, '<mark>', '</mark>') as title_highlight,
                highlight(patents_fts, 1, '<mark>', '</mark>') as abstract_highlight
            FROM patents_fts
            WHERE patents_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "patent_id": row["patent_id"],
                    "title": row["title"],
                    "abstract": row["abstract"],
                    "publication_date": row["publication_date"],
                    "url": row["url"],
                    "title_highlight": row["title_highlight"],
                    "abstract_highlight": row["abstract_highlight"],
                }
            )

        return results

    def create_patent_table(self):
        """特許データ用のテーブルとFTSインデックスを作成"""
        cursor = self.conn.cursor()

        # 特許テーブルを作成
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS patents (
            patent_id TEXT PRIMARY KEY,
            title TEXT,
            abstract TEXT,
            publication_date TEXT,
            url TEXT
        )
        """)

        # FTSテーブルを作成
        cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS patents_fts USING fts5(
            title,
            abstract,
            publication_date,
            url,
            patent_id UNINDEXED,
            content='patents',
            content_rowid='rowid'
        )
        """)

        # FTSテーブル更新用のトリガーを作成 (自動的に FTS table とメインテーブルを同期するため)
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS patents_ai AFTER INSERT ON patents BEGIN
            INSERT INTO patents_fts(rowid, title, abstract, publication_date, url, patent_id)
            VALUES (new.rowid, new.title, new.abstract, new.publication_date, new.url, new.patent_id);
        END;
        """)

        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS patents_ad AFTER DELETE ON patents BEGIN
            INSERT INTO patents_fts(patents_fts, rowid, title, abstract, publication_date, url, patent_id)
            VALUES('delete', old.rowid, old.title, old.abstract, old.publication_date, old.url, old.patent_id);
        END;
        """)

        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS patents_au AFTER UPDATE ON patents BEGIN
            INSERT INTO patents_fts(patents_fts, rowid, title, abstract, publication_date, url, patent_id)
            VALUES('delete', old.rowid, old.title, old.abstract, old.publication_date, old.url, old.patent_id);
            INSERT INTO patents_fts(rowid, title, abstract, publication_date, url, patent_id)
            VALUES (new.rowid, new.title, new.abstract, new.publication_date, new.url, new.patent_id);
        END;
        """)

        self.conn.commit()

    def insert_patents(self, patents: list[dict[str, Any]]):
        """特許データをデータベースに挿入

        Args:
            patents: 特許データのリスト
        """
        cursor = self.conn.cursor()

        for patent in patents:
            # 特許データが既に存在する場合はスキップ
            cursor.execute("SELECT 1 FROM patents WHERE patent_id = ?", (patent["patent_id"],))
            if cursor.fetchone():
                continue

            cursor.execute(
                """
                INSERT INTO patents (patent_id, title, abstract, publication_date, url)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    patent["patent_id"],
                    patent["title"],
                    patent["abstract"],
                    patent["publication_date"],
                    patent.get("url", f"https://patents.google.com/patent/{patent['patent_id']}"),
                ),
            )

        self.conn.commit()

    def get_db_stats(self) -> dict[str, Any]:
        """データベースの統計情報を取得

        Returns:
            統計情報を含む辞書
        """
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM patents")
        total_patents = cursor.fetchone()[0]

        cursor.execute("SELECT MIN(publication_date), MAX(publication_date) FROM patents")
        date_range = cursor.fetchone()

        return {"total_patents": total_patents, "date_range": {"min_date": date_range[0], "max_date": date_range[1]}}

    def close(self):
        """データベース接続を閉じる"""
        self.conn.close()


class KeywordList(BaseModel):
    """特許検索用の複合キーワードリスト"""

    keywords_list: list[list[str]] = Field(
        description="複数キーワードの組み合わせのリスト。各組み合わせは1つ以上のキーワードを含む",
    )
    translated_keywords_list: list[list[str]] = Field(
        description="原言語のキーワードを英語に翻訳した複数キーワードの組み合わせのリスト",
    )


@traceable
async def generate_patent_search_keywords(
    topic: str,
    llm_provider: str = "openai",
    llm_model: str = "gpt-4o",
    llm_model_config: dict[str, Any] | None = None,
) -> KeywordList:
    llm_model_config = llm_model_config or {}
    llm = init_chat_model(model=llm_model, model_provider=llm_provider, **llm_model_config)
    structured_llm = llm.with_structured_output(KeywordList)

    system_prompt = """
    あなたは特許検索のエキスパートです。与えられたトピックに基づいて、Google Patents データベースを検索するための効果的なキーワード組み合わせを生成してください。

    指示:
    1. 検索に適した「キーワードの組み合わせ」を5〜10組生成してください
    2. 各「キーワードの組み合わせ」は、1つ以上のキーワードを含みます (topic そのものをキーワードとすることも許可されています)
    3. 複数のキーワードを含む組み合わせでは、すべてのキーワードがAND条件で検索されます
    4. 原言語（ユーザーが入力した言語）のキーワード組み合わせリストと、それらを英語に翻訳したリストの両方を生成してください
    5. キーワードは具体的かつ技術的である必要があります
    6. 結果が多すぎる一般的な用語は避けてください
    7. topic が単なる技術ワード (ex: 自動運転) の場合は、トピックそのものと英訳のみを返してください。ただし同義語は追加してください

    <example>
    topic:「自動運転車の障害物検知」
    keywords_list: [
        ["自動運転", "障害物検知"],
        ["自律走行", "センサー", "障害物"],
        ["自動運転車", "ライダー"],
        ["自動車", "障害物回避", "AI"], ...
    ]
    translated_keywords_list: [
        ["autonomous driving", "obstacle detection"],
        ["autonomous vehicle", "sensor", "obstacle"],
        ["self-driving car", "LIDAR"],
        ["automobile", "obstacle avoidance", "AI"], ...
    ]

    topic:「自動運転」
    keywords_list: [
        ["自動運転"],
        ["自動運転技術"],
        ["自動運転車"],
        ["自動運転システム"], ...
    ]
    translated_keywords_list: [
        ["autonomous driving"],
        ["autonomous driving technology"],
        ["autonomous vehicle"],
        ["autonomous driving system"], ...
    ]

    topic: 「光格子時計」
    keywords_list: [
        ["光格子時計"],
        ["原始時計"],...
    ]
    translated_keywords_list: [
        ["optical lattice clock"],
        ["atomic clock"],...
    ]
    </example>

    最終的なデータベース検索では、例えば ["自動運転", "障害物検知"] は "(LOWER(title) LIKE LOWER('%自動運転%') AND LOWER(title) LIKE LOWER('%障害物検知%'))"
    という条件に変換されます。
    """

    try:
        response = structured_llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Generate patent search keywords for the following topic: {topic}"),
            ]
        )

        # 空の組み合わせをフィルタリング
        response.keywords_list = [kw_combo for kw_combo in response.keywords_list if kw_combo]
        response.translated_keywords_list = [kw_combo for kw_combo in response.translated_keywords_list if kw_combo]

        # 結果がない場合は単一のキーワードとして元のトピックを使用
        if not response.keywords_list:
            response.keywords_list = [[topic]]
        if not response.translated_keywords_list:
            response.translated_keywords_list = [[topic]]

        return response

    except Exception as e:
        print(f"キーワード生成エラー: {e}")
        default_response = KeywordList(keywords_list=[[topic]], translated_keywords_list=[[topic]])
        return default_response


@traceable
async def search_google_patents(keywords_list: list[list[str]], limit: int = 100) -> list[dict[str, Any]]:
    """BigQueryを使用してGoogle Patents Public Datasetを検索

    Args:
        keywords: 検索キーワード
        limit: 取得する特許の最大数

    Returns:
        特許データのリスト
    """
    client = bigquery.Client()

    where_clauses = []
    for keyword_combo in keywords_list:
        # 各キーワード組み合わせ内の条件（AND）
        and_conditions = []
        for keyword in keyword_combo:
            # SQLインジェクション防止のためのエスケープ
            escaped_keyword = keyword.replace("'", "''")
            condition = (
                f"(LOWER(title) LIKE LOWER('%{escaped_keyword}%') OR LOWER(abstract) LIKE LOWER('%{escaped_keyword}%'))"
            )
            and_conditions.append(condition)

        # 複数のキーワードをANDで結合
        if and_conditions:
            combined_condition = " AND ".join(and_conditions)
            where_clauses.append(f"({combined_condition})")

    where_clause = " OR ".join(where_clauses)

    # SQLクエリを構築
    query = f"""
    WITH base AS (
        SELECT
            publication_number AS patent_id,
            publication_date,
            title,
            abstract,
            url
        FROM
            `patents-public-data.google_patents_research.publications`
        INNER JOIN `patents-public-data.patents.publications` USING(publication_number)
        WHERE
            {where_clause}
            AND LENGTH(title) > 0
            AND LENGTH(abstract) > 0
    )
    SELECT
        base.*
    FROM
        base
    ORDER BY publication_date DESC
    LIMIT {limit}
    """
    try:
        query_job = client.query(query)
        rows = query_job.result()
        patents = []
        for row in rows:
            patent = dict(row.items())
            patents.append(patent)

        return patents
    except Exception as e:
        print(f"BigQuery検索エラー: {e}")
        return []


@traceable
async def initialize_patent_database(
    topic: str,
    db_path: str,
    llm_provider: str,
    llm_model: str,
    llm_model_config: dict | None = None,
    max_results: int = 100,
) -> bool:
    """トピックに基づいて特許データベースを初期化する

    Args:
        topic: 検索トピック
        db_path: SQLiteデータベースのパス
        llm_provider: LLMプロバイダ
        llm_model: LLMモデル名
        llm_model_config: LLMモデルの設定
        max_results: 各キーワードで取得する最大結果数

    Returns:
        初期化が成功したかどうか
    """
    try:
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        retriever = SQLiteFTSPatentetriever(db_path)
        retriever.create_patent_table()

        # キーワードを生成
        keyword_response = await generate_patent_search_keywords(topic, llm_provider, llm_model, llm_model_config)
        print(f"生成されたキーワード組み合わせ (元の言語): {keyword_response.keywords_list}")
        print(f"生成されたキーワード組み合わせ (英語): {keyword_response.translated_keywords_list}")

        # 結合されたキーワードリスト（原言語と英語訳の両方を含む）
        combined_keywords_list = keyword_response.keywords_list + keyword_response.translated_keywords_list

        patents = await search_google_patents(combined_keywords_list, limit=max_results)
        print(f"取得した特許数: {len(patents)}")

        if patents:
            retriever.insert_patents(patents)
            print("特許データベースを更新しました")

        retriever.close()

        return True
    except Exception as e:
        print(f"特許データベース初期化エラー: {e}")
        return False


@traceable
async def patent_search(
    search_queries: list[str],
    db_path: str = "patent_database.sqlite",
    limit: int = 10,
    max_tokens_per_source: int = 8192,
    query_expansion: bool = False,
    **kwargs,
) -> str:
    """特許検索を実行

    Args:
        search_queries: 検索クエリのリスト
        db_path: SQLiteデータベースのパス（デフォルト: "patent_database.sqlite"）
        limit: 各クエリで取得する結果の最大数（デフォルト: 10）

    Returns:
        検索結果の文字列
    """
    search_docs = []
    full_search_queries = []

    # query_expansion: 翻訳や同義語を使ったクエリ拡張 (検索対象が local db であるため、検索回数増加を許容)
    if query_expansion:
        for _query in search_queries:
            expanded_queries = await expand_query(_query)
            full_search_queries.extend(expanded_queries.expanded_queries)
    else:
        full_search_queries = search_queries
    print("search_queries:", full_search_queries)

    try:
        retriever = SQLiteFTSPatentetriever(db_path)

        for query in full_search_queries:
            results = retriever.search(query, limit=limit)

            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "title": result["title"],
                        "url": result["url"],
                        "content": f"Abstract: {result['abstract']}\nPublication Date: {result['publication_date']}",
                        "score": 1.0,  # FTSはスコアを返さないため固定値
                        "raw_content": f"Patent ID: {result['patent_id']}\nTitle: {result['title']}\nAbstract: {result['abstract']}\nPublication Date: {result['publication_date']}",
                    }
                )

            search_docs.append(
                {
                    "query": query,
                    "follow_up_questions": None,
                    "answer": None,
                    "images": [],
                    "results": formatted_results,
                }
            )
    except Exception as e:
        print(f"特許検索エラー: {e}")
        search_docs.append(
            {
                "query": search_queries[0] if search_queries else "",
                "follow_up_questions": None,
                "answer": None,
                "images": [],
                "results": [],
                "error": str(e),
            }
        )
    finally:
        if "retriever" in locals():
            retriever.close()

    return deduplicate_and_format_sources(search_docs, max_tokens_per_source=max_tokens_per_source)
