import hashlib

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from open_deep_researcher.state import Section


def deduplicate_and_format_sources(
    search_response: list,
    max_tokens_per_source: int,
    max_images: int | None = 10,
) -> str:
    """
    Takes a list of search responses and formats them into a readable string.
    Limits the raw_content to approximately max_tokens_per_source tokens.

    Args:
        search_responses: List of search response dicts, each containing:
            - query: str
            - results: List of dicts with fields:
                - title: str
                - url: str
                - content: str
                - score: float
                - raw_content: str|None
        max_tokens_per_source: int
        include_raw_content: bool

    Returns:
        str: Formatted string with deduplicated sources
    """
    # Collect all results
    sources_list, imgs_list = [], []
    for response in search_response:
        sources_list.extend(response["results"])
        imgs_list.extend(response["images"])

    # remove no description images
    imgs_list = [img for img in imgs_list if img["description"] is not None]
    if max_images is not None:
        imgs_list = imgs_list[:max_images]  # 関連度順

    # Maintain original order while deduplicating by content
    unique_sources = []
    seen_contents = set()
    for source in sources_list:
        content = source["content"]
        content_hash = hashlib.md5(content.encode()).hexdigest()

        if content_hash not in seen_contents:
            seen_contents.add(content_hash)
            unique_sources.append(source)

    # Format output
    formatted_text = "Content from sources:\n"
    for source in unique_sources:
        formatted_text += f"{'=' * 80}\n"  # Clear section separator
        formatted_text += f"Source: {source['title']}\n"
        formatted_text += f"{'-' * 80}\n"  # Subsection separator
        formatted_text += f"URL: {source['url']}\n===\n"

        content = source.get("raw_content", None) or source.get("content", "")
        if content:
            char_limit = max_tokens_per_source * 4
            if len(content) > char_limit:
                content = content[:char_limit] + "... [truncated]"
            content = content.replace("\n\n", "\n").strip()
            formatted_text += f"Most relevant content from source ({max_tokens_per_source} limit): {content}\n"

    # add images if available
    if len(imgs_list) > 0:
        formatted_text += f"{'-' * 20}Images{'-' * 20}\n"
        for image in imgs_list:
            url, description = image["url"], image["description"]
            formatted_text += f"- <img src='{url}' alt='{description}'>\n"
    formatted_text += f"{'=' * 80}\n\n"  # End section separator

    return formatted_text.strip()


def get_config_value(value):
    """
    Helper function to handle both string and enum cases of configuration values
    """
    return value if isinstance(value, str) else value.value


def format_sections(sections: list[Section]) -> str:
    """Format a list of sections into a string"""
    formatted_str = ""
    for idx, section in enumerate(sections, 1):
        formatted_str += f"""
{"=" * 60}
Section {idx}: {section.name}
{"=" * 60}
Description:
{section.description}

Content:
{section.content if section.content else "[Not yet written]"}

"""
    return formatted_str


def normalize_heading_level(content, target_level):
    """
    コンテンツ内の見出しレベルを指定のレベルに正規化する
    target_level: 3 なら ### (H3)、4 なら #### (H4) など
    """
    lines = content.split("\n")
    normalized_lines = []

    for line in lines:
        if line.strip().startswith("#"):
            # 現在の見出しレベルを検出
            heading_match = line.lstrip()
            hash_count = 0
            for char in heading_match:
                if char == "#":
                    hash_count += 1
                else:
                    break

            # 見出しテキストを抽出
            heading_text = line.strip()[hash_count:].strip()

            # 指定されたレベルの見出しとして再構築
            normalized_lines.append("#" * target_level + " " + heading_text)
        else:
            normalized_lines.append(line)

    return "\n".join(normalized_lines)


def detect_main_section_level(content):
    """メインセクションの見出しレベルを検出"""

    min_level = 6  # 最も小さい見出しレベルを追跡
    found = False

    # 行ごとにチェック
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("#"):
            # #の個数をカウント
            level = 0
            for char in line:
                if char == "#":
                    level += 1
                else:
                    break

            # 最小レベルを更新
            if level < min_level and level > 0:
                min_level = level
                found = True
    return min_level if found else 2


def count_detail_analysis_sections(content):
    """既存の詳細分析セクションの数を数える"""
    count = 0

    # 正規表現でマッチングするよりも単純に行ごとに確認する方法
    lines = content.split("\n")
    for line in lines:
        line = line.strip()
        # 詳細分析、詳細解析、詳細分析1、詳細分析2などをカウント
        if (
            any(line.endswith(suffix) for suffix in [" 詳細分析", " 詳細解析"])
            or any(line.endswith(f" 詳細分析{i}") for i in range(1, 10))
            or any(line.endswith(f" 詳細解析{i}") for i in range(1, 10))
        ):
            count += 1

    return count


def generate_detail_heading(level, count, section_name):
    """詳細分析セクションの見出しを生成

    Args:
        level: 見出しレベル (# の数)
        count: 詳細分析の番号 (0から始まる)
        section_name: セクション名

    Returns:
        str: 見出し文字列
    """
    # 初回は「{section_name}: 詳細分析」、2回目以降は「{section_name}: 詳細分析1」「{section_name}: 詳細分析2」などインデックス付きで
    if count == 0:
        return "#" * level + f" {section_name}: 詳細分析"
    else:
        return "#" * level + f" {section_name}: 詳細分析{count + 1}"


class ExpandedQuerySet(BaseModel):
    """拡張された検索クエリセット"""

    expanded_queries: list[str] = Field(..., title="拡張された検索クエリのリスト。元のクエリも含む")


async def expand_query(
    query: str,
    max_queries_per_language: int = 2,
    llm_provider: str = "openai",
    llm_model: str = "gpt-4o",
    llm_model_config: dict | None = None,
) -> ExpandedQuerySet:
    llm_model_config = llm_model_config or {}
    llm = init_chat_model(model=llm_model, model_provider=llm_provider, **llm_model_config)
    structured_llm = llm.with_structured_output(ExpandedQuerySet)

    system_prompt = """
    あなたは多言語検索クエリ生成の専門家です。与えられたトピックに基づいて、効果的な検索クエリを生成してください。

    <task>
    1. ユーザーが入力したクエリの同義キーワードを生成します
        - 入力クエリが文章の場合は、メインキーワードを抽出します
        - 入力クエリが複数のキーワードの場合は、全てのキーワードを考慮してください
    2. ユーザーが入力したクエリと同義キーワードを多言語に翻訳します
    3. 入力言語が英語の場合は、日本語に翻訳します
    4. 入力言語が英語以外の場合は、英語に翻訳します
    5. 元のクエリは出力するキーワードリストに必ず含めるようにしてください
    </task>

    言語ごとに**最大 {max_queries_per_language} 件**のクエリを生成してください。

    <example>
    input: "機械学習とはなんですか?"
    output: ["機械学習", "machine learning"]

    input: "画像認識 機械学習モデル"
    output: [
        "画像認識 機械学習モデル",
        "画像認識 ニューラルネット",
        "image recognition machine learning model",
        "image recognition neural network"
    ]

    input: "光格子時計 展望"
    output: [
        "光格子時計 展望",
        "光格子時計 未来",
        "optical lattice clock outlook",
        "optical lattice clock future"
    ]
    </example>
    """

    try:
        response = structured_llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"以下のクエリを拡張してください: {query}"),
            ]
        )

        response.expanded_queries = [q.strip() for q in response.expanded_queries if q.strip()]
        if not response.expanded_queries:
            response.expanded_queries = [query]

        return response

    except Exception as e:
        print(f"クエリ生成エラー: {e}")
        return ExpandedQuerySet(expanded_queries=[query])
