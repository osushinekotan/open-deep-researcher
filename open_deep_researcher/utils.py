from open_deep_researcher.retriever.hybrid import hybrid_search
from open_deep_researcher.retriever.local import local_search
from open_deep_researcher.retriever.web import web_search
from open_deep_researcher.state import Section


def get_config_value(value):
    """
    Helper function to handle both string and enum cases of configuration values
    """
    return value if isinstance(value, str) else value.value


async def select_and_execute_search(
    search_source: str,
    query_list: list[str],
    web_config: dict = None,
    local_config: dict = None,
) -> str:
    """適切な検索ソースを選択して実行する

    Args:
        search_source: 検索ソース（"web", "local", "hybrid"）
        query_list: 検索クエリのリスト
        web_config: Webプロバイダーの設定パラメータ
        local_config: ローカル検索の設定パラメータ

    Returns:
        検索結果の文字列
    """
    # デフォルト値の設定
    web_config = web_config or {}
    local_config = local_config or {}

    if search_source == "web":
        # web_config内からproviderを取得して、残りのパラメータを渡す
        provider = web_config.pop("provider", "tavily")
        result = await web_search(provider, query_list, web_config)
        # web_configを元に戻す（副作用を避けるため）
        web_config["provider"] = provider
        return result

    elif search_source == "local":
        return await local_search(query_list, **local_config)

    elif search_source == "hybrid":
        # hybrid検索では、web_configからproviderを取得
        provider = web_config.pop("provider", "tavily")
        return await hybrid_search(
            query_list,
            web_search_api=provider,
            web_search_params=web_config,
            local_search_params=local_config,
        )
    else:
        raise ValueError(f"サポートされていない検索ソース: {search_source}")


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
