import asyncio
from pathlib import Path
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from open_deep_researcher.configuration import Configuration
from open_deep_researcher.prompts import (
    conclusion_writer_instructions,
    deep_research_planner_instructions,
    deep_research_queries_instructions,
    deep_research_writer_instructions,
    introduction_query_writer_instructions,
    introduction_writer_instructions,
    query_writer_instructions,
    question_to_plan_instructions,
    report_planner_instructions,
    report_planner_query_writer_instructions,
    section_grader_instructions,
    section_writer_inputs,
    section_writer_instructions,
)
from open_deep_researcher.retriever.local.full_text_search import initialize_knowledge_base, local_search
from open_deep_researcher.retriever.web import web_search
from open_deep_researcher.state import (
    Feedback,
    Queries,
    ReportState,
    ReportStateInput,
    ReportStateOutput,
    SectionOutputState,
    Sections,
    SectionState,
    SubTopics,
)
from open_deep_researcher.utils import (
    count_detail_analysis_sections,
    detect_main_section_level,
    format_sections,
    generate_detail_heading,
    get_config_value,
    normalize_heading_level,
)

PROVIDER_DESCRIPTIONS = {
    "tavily": "General web search, good for broad information gathering",
    "arxiv": "Academic papers and preprints, best for scientific topics",
    "local": "Search through locally stored documents",
}

QUERY_GNERATION_DESCRIPTION = {
    "tavily": """
<Tavily>
- Natural language focus: Use natural sentence expressions that convey the context of the search subject.
- Utilization of keywords and synonyms: Include main keywords as well as related synonyms and technical terms.
- Concise and clear: Avoid redundant expressions; state the core information clearly.
- Context-dependent expression: Choose expressions suited to the specific field or theme to accurately convey the intended meaning.
</Tavily>
""",
    "arxiv": """
<Arxiv>
- Utilize field specifications: Clearly specify arXiv’s unique search fields such as title, author, and category.
- Use academic terminology: Accurately include specialized and technical terms to narrow down relevant papers.
- Quotation for phrase search: Enclose multi-word phrases in quotation marks to ensure an exact match.
</Arxiv>
""",
    "local": """
1. **SQLite FTS5の検索構文**:
   * 基本的な検索: 単語をスペースで区切る（暗黙的にAND）
   * ブール演算子: AND, OR, NOT (大文字でなければならない)
   * フレーズ検索: 単語を引用符で囲む（例: "exact phrase"）
   * ワイルドカード: 語幹検索に*を使用（例: process*）
   * 近接検索: NEAR/N（例: word1 NEAR/3 word2）- Nは最大単語間距離

2. **検索精度とリコールの最適化**:
   * 重要キーワードを含める（ANDで結合）: keyword1 keyword2
   * 代替表現を使用（ORで結合）: keyword1 OR alternative1
   * 派生形も含める: keyword* で語幹からの派生形もカバー
   * 検索の文脈を明確化: 特定分野内の検索なら分野も含める

3. **プロバイダ固有の最適化**:
    * ブール演算子を活用: `machine AND learning NOT basic`
    * フレーズ検索で正確な一致: `"neural network" NOT "network protocol"`
    * 語形変化対応: `process*`（processes, processing等にマッチ）
    * 複合クエリは丸括弧でグループ化: `(deep OR advanced) AND learning`
    * 同義語を考慮: `(artificial OR computational) intelligence`

4. **検索パターン例**:
   a. 中核概念の単純クエリ: `machine learning`
   b. 代替表現を含むOR拡張クエリ: `"neural network" OR "deep learning"`
   c. 文脈制限クエリ: `python AND "machine learning" NOT statistics`
   d. ワイルドカード活用クエリ: `program* AND analy*`
   e. 概念組み合わせクエリ: `"data preparation" AND model*`
""",
}


def get_provider_config(configurable: Configuration, provider_name: str) -> dict:
    """指定された検索プロバイダの設定を取得する"""

    if provider_name == "tavily":
        return configurable.tavily_search_config or {}
    elif provider_name == "arxiv":
        return configurable.arxiv_search_config or {}
    elif provider_name == "local":
        return configurable.local_search_config or {}
    else:
        # デフォルト設定（空の辞書）を返す
        return {}


## Nodes --


async def setup_knowledge_base(state: ReportState, config: RunnableConfig):
    # Get configuration
    configurable = Configuration.from_runnable_config(config)

    # Skip if local document provider is not available
    if "local" not in configurable.available_search_providers:
        return {"local_db_path": None}

    local_config = configurable.local_search_config or {}
    local_document_path = local_config.get("local_document_path", None)

    # Skip if local documents are not provided
    if not local_document_path:
        return {"local_db_path": None}

    db_path = await initialize_knowledge_base(**local_config)
    return {"local_db_path": db_path}


def extract_urls_from_search_results(source_str: str) -> list[str]:
    """Extract URLs and titles from search results and format as Markdown links.

    Args:
        source_str: Formatted string containing search results

    Returns:
        List of formatted Markdown links from the search results
    """
    markdown_links = []
    lines = source_str.split("\n")
    current_title = ""

    for _, line in enumerate(lines):
        if line.startswith("Source: "):
            current_title = line[8:].strip()

        elif line.startswith("URL: ") and current_title:
            url = line[5:].strip()
            if url:
                # generate link
                markdown_link = f"[{current_title}]({url})"
                if markdown_link not in markdown_links:
                    markdown_links.append(markdown_link)

                # reset title
                current_title = ""

    return markdown_links


async def generate_introduction(state: ReportState, config: RunnableConfig):
    """イントロダクションを生成する"""
    # Inputs
    topic = state["topic"]

    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    number_of_queries = configurable.number_of_queries
    introduction_provider = configurable.introduction_search_provider
    provider_config = get_provider_config(configurable, provider_name=introduction_provider)

    # Set writer model
    writer_provider = get_config_value(configurable.writer_provider)
    writer_model_name = get_config_value(configurable.writer_model)
    writer_model_config = configurable.writer_model_config or {}
    writer_model = init_chat_model(model=writer_model_name, model_provider=writer_provider, **writer_model_config)
    structured_llm = writer_model.with_structured_output(Queries)

    # Format system instructions
    system_instructions_query = introduction_query_writer_instructions.format(
        topic=topic,
        number_of_queries=number_of_queries,
        search_provider=introduction_provider,
    )
    system_instructions_query += f"\n\nPlease respond in **{configurable.language}** language."

    # Generate queries
    results = structured_llm.invoke(
        [
            SystemMessage(content=system_instructions_query),
            HumanMessage(content="Generate search queries that will help with writing an introduction for the report."),
        ]
    )

    # Execute search
    query_list = [query.search_query for query in results.queries]

    if introduction_provider == "local":
        source_str = await local_search(
            query_list=query_list,
            max_tokens_per_source=configurable.max_tokens_per_source,
            **provider_config,
        )
    else:
        source_str = await web_search(
            search_api=introduction_provider,
            query_list=query_list,
            params_to_pass=provider_config,
            max_tokens_per_source=configurable.max_tokens_per_source,
            max_images=0,
        )

    # Extract URLs from search results for references
    urls = extract_urls_from_search_results(source_str)

    # Generate introduction
    system_instructions = introduction_writer_instructions.format(
        topic=topic,
        context=source_str,
        max_words=configurable.max_introduction_words,
    )
    system_instructions += f"\n\nPlease respond in **{configurable.language}** language."

    # Write introduction
    introduction_content = writer_model.invoke(
        [
            SystemMessage(content=system_instructions),
            HumanMessage(content="Write an introduction for the report based on the provided sources."),
        ]
    )

    return {
        "introduction": introduction_content.content,
        "all_urls": urls,
    }


def determine_if_question(state: ReportState, config: RunnableConfig):
    """Determine if the topic is a question."""
    topic = state["topic"]

    # TODO: use LLM to determine if the topic is a question
    is_question = topic.strip().endswith(("?", "？"))  # Simple heuristic
    return {"is_question": is_question}


async def generate_report_plan(state: ReportState, config: RunnableConfig):
    """Generate the initial report plan with sections.

    This node:
    1. Gets configuration for the report structure and search parameters
    2. Generates search queries to gather context for planning
    3. Performs web searches using those queries
    4. Uses an LLM to generate a structured plan with sections

    Args:
        state: Current graph state containing the report topic
        config: Configuration for models, search APIs, etc.

    Returns:
        Dict containing the generated sections
    """
    # Inputs
    topic = state["topic"]
    is_question = state.get("is_question", False)
    feedback = state.get("feedback_on_report_plan", None)
    introduction = state.get("introduction", "")

    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    report_structure = configurable.report_structure
    number_of_queries = configurable.number_of_queries
    max_sections = configurable.max_sections
    planning_provider = configurable.planning_search_provider
    provider_config = get_provider_config(configurable, provider_name=planning_provider)
    available_providers = [provider.value for provider in configurable.available_search_providers]

    # Convert JSON object to string if necessary
    if isinstance(report_structure, dict):
        report_structure = str(report_structure)

    # Set writer model
    writer_provider = get_config_value(configurable.writer_provider)
    writer_model_name = get_config_value(configurable.writer_model)
    writer_model_config = configurable.writer_model_config or {}
    writer_model = init_chat_model(model=writer_model_name, model_provider=writer_provider, **writer_model_config)
    structured_llm = writer_model.with_structured_output(Queries)

    # Format system instructions
    system_instructions_query = report_planner_query_writer_instructions.format(
        topic=topic,
        report_organization=report_structure,
        number_of_queries=number_of_queries,
        search_provider=planning_provider,
    )
    system_instructions_query += f"\n\nPlease respond in **{configurable.language}** language."

    # Generate queries
    results = structured_llm.invoke(
        [
            SystemMessage(content=system_instructions_query),
            HumanMessage(content="Generate search queries that will help with planning the sections of the report."),
        ]
    )

    # Execute search
    query_list = [query.search_query for query in results.queries]

    if planning_provider == "local":
        source_str = await local_search(
            query_list=query_list,
            max_tokens_per_source=configurable.max_tokens_per_source,
            **provider_config,
        )
    else:
        source_str = await web_search(
            search_api=planning_provider,
            query_list=query_list,
            params_to_pass=provider_config,
            max_tokens_per_source=configurable.max_tokens_per_source,
            max_images=0,
        )

    urls = extract_urls_from_search_results(source_str)

    search_provider_descriptions = "\n  ".join(
        [f"- {provider}: {PROVIDER_DESCRIPTIONS.get(provider, '')}" for provider in available_providers]
    )

    # Format system instructions
    if is_question:
        system_instructions_sections = question_to_plan_instructions.format(
            topic=topic,
            report_organization=report_structure,
            context=source_str + "\n\nINTRODUCTION:\n" + introduction if introduction else source_str,
            feedback=feedback,
            available_search_providers=", ".join(available_providers),
            search_provider_descriptions=search_provider_descriptions,
            max_sections=max_sections,
        )
    else:
        system_instructions_sections = report_planner_instructions.format(
            topic=topic,
            report_organization=report_structure,
            context=source_str + "\n\nINTRODUCTION:\n" + introduction if introduction else source_str,
            feedback=feedback,
            available_search_providers=", ".join(available_providers),
            search_provider_descriptions=search_provider_descriptions,
            max_sections=max_sections,
        )
    system_instructions_sections += f"\n\nPlease respond in **{configurable.language}** language."

    # Set the planner
    planner_provider = get_config_value(configurable.planner_provider)
    planner_model = get_config_value(configurable.planner_model)
    planner_model_config = configurable.planner_model_config or {}

    # Report planner instructions
    planner_message = """Generate the sections of the report. Your response must include a 'sections' field containing a list of sections.
                        Each section must have: name, description, plan, research, search_options, and content fields."""

    # With other models, we can use with_structured_output
    planner_llm = init_chat_model(
        model=planner_model,
        model_provider=planner_provider,
        **planner_model_config,
    )

    # Generate the report sections
    structured_llm = planner_llm.with_structured_output(Sections)
    report_sections = structured_llm.invoke(
        [
            SystemMessage(content=system_instructions_sections),
            HumanMessage(content=planner_message),
        ]
    )

    # Get sections
    sections = report_sections.sections
    default_provider = configurable.default_search_provider.value
    # search_options が空の場合は、デフォルト値を設定
    for section in sections:
        if not hasattr(section, "search_options") or not section.search_options:
            section.search_options = [default_provider]

    sections = [s for s in sections if s.name.lower() != "conclusion"]
    return {"sections": sections, "is_question": is_question, "all_urls": urls}


def human_feedback(
    state: ReportState, config: RunnableConfig
) -> Command[Literal["generate_report_plan", "build_section_with_research"]]:
    """Get human feedback on the report plan and route to next steps.

    This node:
    1. Formats the current report plan for human review
    2. Gets feedback via an interrupt
    3. Routes to either:
       - Section writing if plan is approved
       - Plan regeneration if feedback is provided

    Args:
        state: Current graph state with sections to review
        config: Configuration for the workflow

    Returns:
        Command to either regenerate plan or start section writing
    """
    # Get sections
    topic = state["topic"]
    sections = state["sections"]

    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    available_providers = [provider.value for provider in configurable.available_search_providers]
    for section in sections:
        # 不正なプロバイダをフィルタリング
        section.search_options = [provider for provider in section.search_options if provider in available_providers]

        # 検索オプションが空の場合、デフォルトプロバイダを追加
        if not section.search_options:
            section.search_options = [configurable.default_search_provider.value]

    # Check if we should skip human feedback
    if configurable.skip_human_feedback:
        # Skip the interrupt and go straight to section writing
        return Command(
            goto=[
                Send(
                    "build_section_with_research",
                    {"topic": topic, "section": s, "search_iterations": 0},
                )
                for s in sections
            ]
        )

    # 各セクションの情報を詳細に表示
    sections_str = "\n\n".join(
        f"セクション: {section.name}\n説明: {section.description}\n検索オプション: {', '.join(section.search_options)}"
        for section in sections
    )

    # レポート計画に関するフィードバックを取得
    interrupt_message = f"""以下のレポート計画についてフィードバックしてください。
                        \n\n{sections_str}\n
                        \nレポート計画は要件を満たしていますか？
                        \n計画を承認する場合は 'true' を入力してください。
                        \n計画を再生成するためのフィードバックを提供する場合は、具体的な指示（セクションの追加・削除・変更、検索オプションの調整など）を入力してください:"""

    feedback = interrupt(interrupt_message)

    # If the user approves the report plan, kick off section writing
    if isinstance(feedback, bool) and feedback is True:
        return Command(
            goto=[
                Send(
                    "build_section_with_research",
                    {"topic": topic, "section": s, "search_iterations": 0},
                )
                for s in sections
            ]
        )

    # If the user provides feedback, regenerate the report plan
    elif isinstance(feedback, str):
        # Treat this as feedback
        return Command(goto="generate_report_plan", update={"feedback_on_report_plan": feedback})
    else:
        raise TypeError(f"Interrupt value of type {type(feedback)} is not supported.")


def generate_queries(state: SectionState, config: RunnableConfig):
    """各検索プロバイダごとに検索クエリを生成する"""
    # Get state
    topic = state["topic"]
    section = state["section"]
    search_options = section.search_options

    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    number_of_queries = configurable.number_of_queries
    available_providers = [provider.value for provider in configurable.available_search_providers]
    # 利用可能なプロバイダのみをフィルタリング
    search_options = [provider for provider in search_options if provider in available_providers]
    if not search_options:
        search_options = [configurable.default_search_provider.value]

    # Generate queries for each provider
    writer_provider = get_config_value(configurable.writer_provider)
    writer_model_name = get_config_value(configurable.writer_model)
    writer_model_config = configurable.writer_model_config or {}
    writer_model = init_chat_model(model=writer_model_name, model_provider=writer_provider, **writer_model_config)
    structured_llm = writer_model.with_structured_output(Queries)

    search_queries_by_provider = {}

    for provider in search_options:
        # Format system instructions for this provider
        query_generation_description = QUERY_GNERATION_DESCRIPTION.get(provider, "")
        assert query_generation_description, f"Query generation description not found for provider: {provider}"

        system_instructions = query_writer_instructions.format(
            topic=topic,
            section_topic=section.description,
            search_provider=provider,
            number_of_queries=number_of_queries,
            query_generation_description=query_generation_description,
        )
        system_instructions += f"\n\nPlease respond in **{configurable.language}** language."

        # Generate queries for this provider
        queries = structured_llm.invoke(
            [
                SystemMessage(content=system_instructions),
                HumanMessage(content=f"Generate search queries optimized for {provider} search on the provided topic."),
            ]
        )

        search_queries_by_provider[provider] = queries.queries

    return {"search_queries_by_provider": search_queries_by_provider}


async def search(state: SectionState, config: RunnableConfig):  # noqa: C901
    """各プロバイダで検索を実行し、結果を統合する"""
    # Get state
    search_queries_by_provider = state["search_queries_by_provider"]
    section = state["section"]
    search_options = section.search_options

    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    max_tokens_per_source = configurable.max_tokens_per_source
    request_delay = getattr(configurable, "request_delay", 0.0)
    if request_delay > 0:
        print(f"Applying request delay of {request_delay} seconds...")
        await asyncio.sleep(request_delay)

    # 各プロバイダごとに検索実行
    search_results_by_provider = {}
    all_urls = []

    for provider in search_options:
        try:
            queries = search_queries_by_provider.get(provider, [])
            if not queries:
                continue

            query_list = [query.search_query for query in queries]

            # プロバイダごとの設定を取得
            if provider == "tavily":
                search_result = await web_search(
                    "tavily",
                    query_list,
                    params_to_pass=get_provider_config(configurable, provider),
                    max_tokens_per_source=max_tokens_per_source,
                )
            elif provider == "arxiv":
                search_result = await web_search(
                    "arxiv",
                    query_list,
                    params_to_pass=get_provider_config(configurable, provider),
                    max_tokens_per_source=max_tokens_per_source,
                )
            elif provider == "local":
                search_result = await local_search(
                    query_list,
                    max_tokens_per_source=max_tokens_per_source,
                    **get_provider_config(configurable, provider),
                )
            else:
                continue

            search_results_by_provider[provider] = search_result

            # URLを収集
            provider_urls = extract_urls_from_search_results(search_result)
            all_urls.extend(provider_urls)

        except Exception as e:
            print(f"プロバイダ '{provider}' の検索中にエラーが発生しました: {str(e)}")
            search_results_by_provider[provider] = f"エラー: {str(e)}"

    # 全プロバイダの結果を結合
    combined_results = "\n\n".join(
        [f"=== {provider} SEARCH RESULTS ===\n{result}" for provider, result in search_results_by_provider.items()]
    )

    return {
        "source_str": combined_results,
        "search_results_by_provider": search_results_by_provider,
        "search_iterations": state["search_iterations"] + 1,
        "all_urls": all_urls,
    }


async def write_section(state: SectionState, config: RunnableConfig) -> Command[Literal[END, "search"]]:
    """Write a section of the report and evaluate if more research is needed.

    This node:
    1. Writes section content using search results
    2. Evaluates the quality of the section
    3. Either:
       - Completes the section if quality passes
       - Triggers more research if quality fails

    Args:
        state: Current state with search results and section info
        config: Configuration for writing and evaluation

    Returns:
        Command to either complete section or do more research
    """
    # Get state
    topic = state["topic"]
    section = state["section"]
    source_str = state["source_str"]
    all_urls = state["all_urls"]

    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    request_delay = getattr(configurable, "request_delay", 0.0)
    if request_delay > 0:
        print(f"Applying request delay of {request_delay} seconds...")
        await asyncio.sleep(request_delay)

    # Format system instructions
    section_writer_inputs_formatted = section_writer_inputs.format(
        topic=topic,
        section_name=section.name,
        section_topic=section.description,
        context=source_str,
        section_content=section.content,
    )

    # Generate section
    writer_provider = get_config_value(configurable.writer_provider)
    writer_model_name = get_config_value(configurable.writer_model)
    writer_model_config = configurable.writer_model_config or {}
    writer_model = init_chat_model(model=writer_model_name, model_provider=writer_provider, **writer_model_config)
    section_content = writer_model.invoke(
        [
            SystemMessage(content=section_writer_instructions.format(max_words=configurable.max_section_words)),
            HumanMessage(content=section_writer_inputs_formatted),
        ]
    )

    # Write content to the section object
    section.content = section_content.content

    # Grade prompt
    section_grader_message = """Grade the report and consider follow-up questions for missing information.
                               If the grade is 'pass', return empty strings for all follow-up queries.
                               If the grade is 'fail', provide specific search queries to gather missing information."""

    section_grader_instructions_formatted = section_grader_instructions.format(
        topic=topic,
        section_topic=section.description,
        section=section.content,
        number_of_follow_up_queries=configurable.number_of_queries,
    )

    # Use planner model for reflection
    planner_provider = get_config_value(configurable.planner_provider)
    planner_model = get_config_value(configurable.planner_model)
    planner_model_config = configurable.planner_model_config or {}
    reflection_model = init_chat_model(
        model=planner_model,
        model_provider=planner_provider,
        **planner_model_config,
    ).with_structured_output(Feedback)

    # Generate feedback
    feedback = reflection_model.invoke(
        [
            SystemMessage(content=section_grader_instructions_formatted),
            HumanMessage(content=section_grader_message),
        ]
    )

    # If the section is passing or the max search depth is reached
    if feedback.grade == "pass" or state["search_iterations"] >= configurable.max_reflection:
        # Publish the section and URLs
        return Command(update={"completed_sections": [section], "all_urls": all_urls}, goto=END)
    else:
        return Command(
            update={"section": section, "all_urls": all_urls},
            goto="search",
        )


def generate_conclusion(state: ReportState, config: RunnableConfig):
    """Write a conclusion based on all completed sections.

    Args:
        state: Current state with all completed sections
        config: Configuration for the conclusion writer model

    Returns:
        Dict with the written conclusion section
    """
    # Get configuration
    configurable = Configuration.from_runnable_config(config)

    # Get state
    topic = state["topic"]
    is_question = state.get("is_question", False)
    completed_sections = state["completed_sections"]

    # Format sections content
    sections_content = format_sections(completed_sections)

    # Format instructions
    system_instructions = conclusion_writer_instructions.format(
        topic=topic,
        is_question=is_question,
        sections_content=sections_content,
        max_words=configurable.max_conclusion_words,
    )
    system_instructions += f"\n\nPlease respond in **{configurable.language}** language."

    # Use the conclusion writer model if specified, otherwise use the regular writer model
    writer_provider = get_config_value(configurable.conclusion_writer_provider)
    writer_model_name = get_config_value(configurable.conclusion_writer_model)
    writer_model_config = configurable.conclusion_writer_model_config or {}
    writer_model = init_chat_model(model=writer_model_name, model_provider=writer_provider, **writer_model_config)

    # Generate conclusion
    conclusion_content = writer_model.invoke(
        [
            SystemMessage(content=system_instructions),
            HumanMessage(content="Write a conclusion for this report based on the provided sections."),
        ]
    )

    return {"conclusion": conclusion_content.content}


def gather_completed_sections(state: ReportState):
    """Format completed sections as context for writing final sections.

    This node takes all completed research sections and formats them into
    a single context string for writing summary sections.

    Args:
        state: Current state with completed sections

    Returns:
        Dict with formatted sections as context
    """
    # List of completed sections
    completed_sections = state["completed_sections"]

    # Format completed section to str to use as context for final sections
    completed_report_sections = format_sections(completed_sections)

    return {"report_sections_from_research": completed_report_sections}


def compile_final_report(state: ReportState):
    """Compile all sections into the final report with references."""
    # Get sections
    sections = state["sections"]
    completed_sections = {s.name: s.content for s in state["completed_sections"]}
    introduction = state.get("introduction", "")
    conclusion = state.get("conclusion", "")
    all_urls = state.get("all_urls", [])

    # Compile report parts
    report_parts = []

    # Add introduction if available
    if introduction:
        introduction = f"## Introduction\n\n{introduction}"
        report_parts.append(introduction)

    # Add all sections
    for section in sections:
        section.content = completed_sections[section.name]
        report_parts.append(section.content)

    # Add conclusion if available
    if conclusion:
        conclusion = f"## Conclusion\n\n{conclusion}"
        report_parts.append(conclusion)

    # Add references section
    if all_urls:
        # deduplicate URLs
        dedup_all_urls = list(dict.fromkeys(all_urls))
        references = "## References\n\n"
        for i, url in enumerate(dedup_all_urls, 1):
            references += f"* [{i}] {url}\n"
        report_parts.append(references)

    all_sections = "\n\n".join(report_parts)
    return {"final_report": all_sections}


# Deep research node --


def deep_research_planner(state: SectionState, config: RunnableConfig):
    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    breadth = configurable.deep_research_breadth

    # Get state
    topic = state["topic"]
    section = state["section"]
    current_depth = state.get("current_depth", 0)

    # Get planner model
    planner_provider = get_config_value(configurable.planner_provider)
    planner_model = get_config_value(configurable.planner_model)
    planner_model_config = configurable.planner_model_config or {}
    planner_llm = init_chat_model(
        model=planner_model,
        model_provider=planner_provider,
        **planner_model_config,
    )
    configurable = Configuration.from_runnable_config(config)
    deep_research_providers = configurable.deep_research_providers

    system_instructions = deep_research_planner_instructions.format(
        topic=topic,
        section_name=section.name,
        section_content=section.content,
        current_depth=current_depth,
        breadth=breadth,
        search_providers=", ".join(
            [provider.value if hasattr(provider, "value") else str(provider) for provider in deep_research_providers]
        ),
    )
    system_instructions += f"\n\nPlease respond in **{configurable.language}** language."

    # Generate subtopics
    subtopics_response = planner_llm.with_structured_output(SubTopics).invoke(
        [
            SystemMessage(content=system_instructions),
            HumanMessage(content="セクションの内容に基づいて、掘り下げるべきサブトピックを特定してください。"),
        ]
    )

    return {"deep_research_topics": subtopics_response.subtopics, "current_depth": current_depth + 1}


def generate_deep_research_queries(state: SectionState, config: RunnableConfig):
    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    number_of_queries = configurable.number_of_queries

    # Get state
    topic = state["topic"]
    section = state["section"]
    subtopics = state["deep_research_topics"]

    # 検索プロバイダを取得
    deep_research_providers = configurable.deep_research_providers

    # Get writer model
    writer_provider = get_config_value(configurable.writer_provider)
    writer_model_name = get_config_value(configurable.writer_model)
    writer_model_config = configurable.writer_model_config or {}
    writer_model = init_chat_model(model=writer_model_name, model_provider=writer_provider, **writer_model_config)

    # 各サブトピックとプロバイダのペアごとにクエリを生成
    queries_by_subtopic = {}
    for subtopic in subtopics:
        subtopic_queries = []

        for provider in deep_research_providers:
            query_generation_description = QUERY_GNERATION_DESCRIPTION.get(provider, "")
            assert query_generation_description, f"Query generation description not found for provider: {provider}"
            system_instructions = deep_research_queries_instructions.format(
                topic=topic,
                section_name=section.name,
                subtopic_name=subtopic.name,
                subtopic_description=subtopic.description,
                search_provider=provider,
                number_of_queries=number_of_queries,
                query_generation_description=query_generation_description,
            )
            system_instructions += f"\n\nPlease respond in **{configurable.language}** language."

            structured_llm = writer_model.with_structured_output(Queries)
            queries = structured_llm.invoke(
                [
                    SystemMessage(content=system_instructions),
                    HumanMessage(content=f"このサブトピックに関する{provider}検索用のクエリを生成してください。"),
                ]
            )

            # このプロバイダのクエリを追加
            subtopic_queries.extend(queries.queries)

        queries_by_subtopic[subtopic.name] = subtopic_queries
    return {"deep_research_queries": queries_by_subtopic}


async def deep_research_search(state: SectionState, config: RunnableConfig):
    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    queries_by_subtopic = state["deep_research_queries"]
    request_delay = getattr(configurable, "request_delay", 0.0)
    if request_delay > 0:
        print(f"Applying request delay of {request_delay} seconds...")
        await asyncio.sleep(request_delay)

    # セクションの検索オプションを取得（ここでは深掘り検索用のプロバイダを定義可能）
    # 深掘り検索用に特定のプロバイダを使用するか、セクションの既存オプションを使用
    deep_research_providers = configurable.deep_research_providers

    # 各サブトピックごとに検索を実行
    results_by_subtopic = {}
    all_urls = []
    for subtopic_name, queries in queries_by_subtopic.items():
        query_list = [query.search_query for query in queries]

        # 複数プロバイダの結果を結合
        subtopic_results = []
        for provider in deep_research_providers:
            try:
                # プロバイダごとの設定を取得
                provider_config = get_provider_config(configurable, provider_name=provider)

                # 適切な検索関数を呼び出す
                if provider == "local":
                    result = await local_search(
                        query_list=query_list,
                        max_tokens_per_source=configurable.max_tokens_per_source,
                        **provider_config,
                    )
                else:
                    result = await web_search(
                        search_api=provider,
                        query_list=query_list,
                        params_to_pass=provider_config,
                        max_tokens_per_source=configurable.max_tokens_per_source,
                    )

                extracted_urls = extract_urls_from_search_results(result)
                all_urls.extend(extracted_urls)
                subtopic_results.append(result)
            except Exception as e:
                print(f"deep research '{provider}' の使用中にエラーが発生しました: {str(e)}")

        # 結果を結合
        results_by_subtopic[subtopic_name] = "\n\n".join(subtopic_results)

    return {"deep_research_results": results_by_subtopic, "all_urls": all_urls}


def deep_research_writer(state: SectionState, config: RunnableConfig):
    configurable = Configuration.from_runnable_config(config)
    max_depth = configurable.deep_research_depth

    topic = state["topic"]
    section = state["section"]
    current_depth = state["current_depth"]
    results_by_subtopic = state["deep_research_results"]
    all_urls = state["all_urls"] or []

    writer_provider = get_config_value(configurable.writer_provider)
    writer_model_name = get_config_value(configurable.writer_model)
    writer_model_config = configurable.writer_model_config or {}
    writer_model = init_chat_model(model=writer_model_name, model_provider=writer_provider, **writer_model_config)

    subsections = []
    for subtopic, search_results in results_by_subtopic.items():
        system_instructions = deep_research_writer_instructions.format(
            topic=topic,
            section_name=section.name,
            subtopic=subtopic,
            search_results=search_results,
            max_words=configurable.max_subsection_words,
        )
        system_instructions += f"\n\nPlease respond in **{configurable.language}** language."

        subsection_content = writer_model.invoke(
            [
                SystemMessage(content=system_instructions),
                HumanMessage(content="検索結果に基づいてサブセクションを作成してください。"),
            ]
        )
        subsections.append(subsection_content.content)

    # Update section content with subsections
    updated_content = section.content.strip()
    main_heading_level = detect_main_section_level(updated_content)
    subsection_level = main_heading_level + 1
    detail_heading_level = main_heading_level  # 詳細分析セクションの見出しレベル（通常はメインと同じ）

    # 見出しレベルを正規化し、サブセクションを追加
    normalized_subsections = []
    for subsection in subsections:
        normalized_subsections.append(normalize_heading_level(subsection, subsection_level))
    formatted_subsections = "\n\n".join(normalized_subsections)

    # 詳細分析セクション数に基づいて詳細分析セクションの見出しを生成
    detail_count = count_detail_analysis_sections(updated_content)
    detail_heading = generate_detail_heading(level=detail_heading_level, count=detail_count, section_name=section.name)
    updated_content += "\n\n" + detail_heading + "\n\n" + formatted_subsections

    # update section with new content
    updated_section = section.copy()
    updated_section.content = updated_content

    if current_depth >= max_depth:
        return Command(update={"completed_sections": [updated_section], "all_urls": all_urls}, goto=END)
    else:
        return Command(
            update={"section": updated_section, "current_depth": current_depth, "all_urls": all_urls},
            goto="deep_research_planner",
        )


def cleanup(state: ReportState):
    db_path = state.get("local_db_path")
    if not db_path:
        return {}

    db_path = Path(db_path)
    db_path.unlink(missing_ok=True)
    return {}


# Report section sub-graph --

# Add nodes
section_builder = StateGraph(SectionState, output=SectionOutputState)
section_builder.add_node("generate_queries", generate_queries)
section_builder.add_node("search", search)
section_builder.add_node("write_section", write_section)

section_builder.add_node("deep_research_planner", deep_research_planner)
section_builder.add_node("generate_deep_research_queries", generate_deep_research_queries)
section_builder.add_node("deep_research_search", deep_research_search)
section_builder.add_node("deep_research_writer", deep_research_writer)

section_builder.add_edge(START, "generate_queries")
section_builder.add_edge("generate_queries", "search")
section_builder.add_edge("search", "write_section")


def should_deep_research(state: SectionState, config: RunnableConfig) -> str:
    """深掘り調査を行うかどうかを決定する関数"""
    configurable = Configuration.from_runnable_config(config)
    if getattr(configurable, "enable_deep_research", False):
        return "deep_research_planner"
    return END


# add deep research subgraph to section builder if deep research is enabled
section_builder.add_conditional_edges(
    "write_section",
    should_deep_research,
    ["deep_research_planner", END],
)
section_builder.add_edge("deep_research_planner", "generate_deep_research_queries")
section_builder.add_edge("generate_deep_research_queries", "deep_research_search")
section_builder.add_edge("deep_research_search", "deep_research_writer")
section_builder.add_edge("deep_research_writer", END)

# Outer graph for initial report plan compiling results from each section --

# Add nodes
builder = StateGraph(
    ReportState,
    input=ReportStateInput,
    output=ReportStateOutput,
    config_schema=Configuration,
)
builder.add_node("setup_knowledge_base", setup_knowledge_base)
builder.add_node("determine_if_question", determine_if_question)
builder.add_node("generate_introduction", generate_introduction)
builder.add_node("generate_report_plan", generate_report_plan)
builder.add_node("human_feedback", human_feedback)
builder.add_node("build_section_with_research", section_builder.compile())
builder.add_node("gather_completed_sections", gather_completed_sections)
builder.add_node("compile_final_report", compile_final_report)
builder.add_node("generate_conclusion", generate_conclusion)
builder.add_node("cleanup", cleanup)


# Add edges
builder.add_edge(START, "setup_knowledge_base")
builder.add_edge("setup_knowledge_base", "determine_if_question")
builder.add_edge("determine_if_question", "generate_introduction")
builder.add_edge("generate_introduction", "generate_report_plan")
builder.add_edge("generate_report_plan", "human_feedback")
builder.add_edge("build_section_with_research", "gather_completed_sections")
builder.add_edge("gather_completed_sections", "generate_conclusion")
builder.add_edge("generate_conclusion", "compile_final_report")
builder.add_edge("compile_final_report", "cleanup")
builder.add_edge("cleanup", END)

graph = builder.compile()
