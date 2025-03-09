from typing import Any

from open_deep_researcher.state import Section


def get_config_value(value):
    """
    Helper function to handle both string and enum cases of configuration values
    """
    return value if isinstance(value, str) else value.value


def get_search_params(search_api: str, search_api_config: dict[str, Any] | None) -> dict[str, Any]:
    """
    Filters the search_api_config dictionary to include only parameters accepted by the specified search API.

    Args:
        search_api (str): The search API identifier (e.g., "exa", "tavily").
        search_api_config (Optional[Dict[str, Any]]): The configuration dictionary for the search API.

    Returns:
        Dict[str, Any]: A dictionary of parameters to pass to the search function.
    """
    # Define accepted parameters for each search API
    SEARCH_API_PARAMS = {
        "exa": [
            "max_characters",
            "num_results",
            "include_domains",
            "exclude_domains",
            "subpages",
        ],
        "tavily": [
            "max_results",
            "include_raw_content",
        ],  # Tavily currently accepts no additional parameters
        "perplexity": [],  # Perplexity accepts no additional parameters
        "arxiv": ["load_max_docs", "get_full_documents", "load_all_available_meta"],
        "pubmed": ["top_k_results", "email", "api_key", "doc_content_chars_max"],
        "linkup": ["depth"],
    }

    # Get the list of accepted parameters for the given search API
    accepted_params = SEARCH_API_PARAMS.get(search_api, [])

    # If no config provided, return an empty dict
    if not search_api_config:
        return {}

    # Filter the config to only include accepted parameters
    return {k: v for k, v in search_api_config.items() if k in accepted_params}


def deduplicate_and_format_sources(search_response, max_tokens_per_source, include_raw_content=True):
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
    sources_list = []
    for response in search_response:
        sources_list.extend(response["results"])

    # Deduplicate by URL
    unique_sources = {source["url"]: source for source in sources_list}

    # Format output
    formatted_text = "Content from sources:\n"
    for _, source in enumerate(unique_sources.values(), 1):
        formatted_text += f"{'=' * 80}\n"  # Clear section separator
        formatted_text += f"Source: {source['title']}\n"
        formatted_text += f"{'-' * 80}\n"  # Subsection separator
        formatted_text += f"URL: {source['url']}\n===\n"
        formatted_text += f"Most relevant content from source: {source['content']}\n===\n"
        if include_raw_content:
            # Using rough estimate of 4 characters per token
            char_limit = max_tokens_per_source * 4
            # Handle None raw_content
            raw_content = source.get("raw_content", "")
            if raw_content is None:
                raw_content = ""
                print(f"Warning: No raw_content found for source {source['url']}")
            if len(raw_content) > char_limit:
                raw_content = raw_content[:char_limit] + "... [truncated]"
            formatted_text += f"Full source content limited to {max_tokens_per_source} tokens: {raw_content}\n\n"
        formatted_text += f"{'=' * 80}\n\n"  # End section separator

    return formatted_text.strip()


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
