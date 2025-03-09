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
    get_search_params,
    normalize_heading_level,
    select_and_execute_search,
)

## Nodes --


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
    """Generate an introduction for the report.

    This node:
    1. Generates search queries to gather background information
    2. Performs web searches using those queries
    3. Uses an LLM to generate an introduction based on search results

    Args:
        state: Current graph state containing the report topic
        config: Configuration for models, search APIs, etc.

    Returns:
        Dict containing the generated introduction and collected URLs
    """
    # Inputs
    topic = state["topic"]

    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    number_of_queries = configurable.number_of_queries
    search_api = get_config_value(configurable.search_api)
    search_api_config = configurable.search_api_config or {}
    params_to_pass = get_search_params(search_api, search_api_config)

    # Set writer model (model used for query writing)
    writer_provider = get_config_value(configurable.writer_provider)
    writer_model_name = get_config_value(configurable.writer_model)
    writer_model_config = configurable.writer_model_config or {}
    writer_model = init_chat_model(model=writer_model_name, model_provider=writer_provider, **writer_model_config)
    structured_llm = writer_model.with_structured_output(Queries)

    # Format system instructions
    system_instructions_query = introduction_query_writer_instructions.format(
        topic=topic,
        number_of_queries=number_of_queries,
    )
    system_instructions_query += f"\n\nPlease respond in **{configurable.language}** language."

    # Generate queries
    results = structured_llm.invoke(
        [
            SystemMessage(content=system_instructions_query),
            HumanMessage(content="Generate search queries that will help with writing an introduction for the report."),
        ]
    )

    # Web search
    query_list = [query.search_query for query in results.queries]
    source_str = await select_and_execute_search(search_api, query_list, params_to_pass)

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
    is_question = state.get("is_question", False)  # default to False = report
    feedback = state.get("feedback_on_report_plan", None)
    introduction = state.get("introduction", "")

    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    report_structure = configurable.report_structure
    number_of_queries = configurable.number_of_queries
    search_api = get_config_value(configurable.search_api)
    search_api_config = configurable.search_api_config or {}  # Get the config dict, default to empty
    params_to_pass = get_search_params(search_api, search_api_config)  # Filter parameters

    # Convert JSON object to string if necessary
    if isinstance(report_structure, dict):
        report_structure = str(report_structure)

    # Set writer model (model used for query writing)
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
    )
    system_instructions_query += f"\n\nPlease respond in **{configurable.language}** language."

    # Generate queries
    results = structured_llm.invoke(
        [
            SystemMessage(content=system_instructions_query),
            HumanMessage(content="Generate search queries that will help with planning the sections of the report."),
        ]
    )

    # Web search
    query_list = [query.search_query for query in results.queries]

    # Search the web with parameters
    source_str = await select_and_execute_search(search_api, query_list, params_to_pass)
    urls = extract_urls_from_search_results(source_str)

    # Format system instructions
    if is_question:
        system_instructions_sections = question_to_plan_instructions.format(
            topic=topic,
            report_organization=report_structure,
            context=source_str + "\n\nINTRODUCTION:\n" + introduction if introduction else source_str,
            feedback=feedback,
        )
    else:
        system_instructions_sections = report_planner_instructions.format(
            topic=topic,
            report_organization=report_structure,
            context=source_str + "\n\nINTRODUCTION:\n" + introduction if introduction else source_str,
            feedback=feedback,
        )
    system_instructions_sections += f"\n\nPlease respond in **{configurable.language}** language."

    # Set the planner
    planner_provider = get_config_value(configurable.planner_provider)
    planner_model = get_config_value(configurable.planner_model)
    planner_model_config = configurable.planner_model_config or {}

    # Report planner instructions
    planner_message = """Generate the sections of the report. Your response must include a 'sections' field containing a list of sections.
                        Each section must have: name, description, plan, research, and content fields."""

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

    sections = [s for s in sections if s.name.lower() != "conclusion"]
    return {"sections": sections, "is_question": is_question, "all_urls": urls}


def human_feedback(
    state: ReportState, config: RunnableConfig
) -> Command[Literal["generate_report_plan", "build_section_with_web_research"]]:
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

    # Check if we should skip human feedback
    if configurable.skip_human_feedback:
        # Skip the interrupt and go straight to section writing
        return Command(
            goto=[
                Send(
                    "build_section_with_web_research",
                    {"topic": topic, "section": s, "search_iterations": 0},
                )
                for s in sections
            ]
        )

    sections_str = "\n\n".join(
        f"Section: {section.name}\n" f"Description: {section.description}\n" for section in sections
    )

    # Get feedback on the report plan from interrupt
    interrupt_message = f"""Please provide feedback on the following report plan.
                        \n\n{sections_str}\n
                        \nDoes the report plan meet your needs?\nPass 'true' to approve the report plan.\nOr, provide feedback to regenerate the report plan:"""

    feedback = interrupt(interrupt_message)

    # If the user approves the report plan, kick off section writing
    if isinstance(feedback, bool) and feedback is True:
        # Treat this as approve and kick off section writing
        return Command(
            goto=[
                Send(
                    "build_section_with_web_research",
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
    """Generate search queries for researching a specific section.

    This node uses an LLM to generate targeted search queries based on the
    section topic and description.

    Args:
        state: Current state containing section details
        config: Configuration including number of queries to generate

    Returns:
        Dict containing the generated search queries
    """
    # Get state
    topic = state["topic"]
    section = state["section"]

    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    number_of_queries = configurable.number_of_queries

    # Generate queries
    writer_provider = get_config_value(configurable.writer_provider)
    writer_model_name = get_config_value(configurable.writer_model)
    writer_model_config = configurable.writer_model_config or {}
    writer_model = init_chat_model(model=writer_model_name, model_provider=writer_provider, **writer_model_config)
    structured_llm = writer_model.with_structured_output(Queries)

    # Format system instructions
    system_instructions = query_writer_instructions.format(
        topic=topic,
        section_topic=section.description,
        number_of_queries=number_of_queries,
    )
    system_instructions += f"\n\nPlease respond in **{configurable.language}** language."

    # Generate queries
    queries = structured_llm.invoke(
        [
            SystemMessage(content=system_instructions),
            HumanMessage(content="Generate search queries on the provided topic."),
        ]
    )

    return {"search_queries": queries.queries}


async def search_web(state: SectionState, config: RunnableConfig):
    """Execute web searches for the section queries.

    This node:
    1. Takes the generated queries
    2. Executes searches using configured search API
    3. Formats results into usable context

    Args:
        state: Current state with search queries
        config: Search API configuration

    Returns:
        Dict with search results and updated iteration count
    """
    # Get state
    search_queries = state["search_queries"]

    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    search_api = get_config_value(configurable.search_api)
    search_api_config = configurable.search_api_config or {}  # Get the config dict, default to empty
    params_to_pass = get_search_params(search_api, search_api_config)  # Filter parameters

    # Web search
    query_list = [query.search_query for query in search_queries]

    # Search the web with parameters
    source_str = await select_and_execute_search(search_api, query_list, params_to_pass)
    urls = extract_urls_from_search_results(source_str)

    return {
        "source_str": source_str,
        "search_iterations": state["search_iterations"] + 1,
        "all_urls": urls,
    }


def write_section(state: SectionState, config: RunnableConfig) -> Command[Literal[END, "search_web"]]:
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
    urls = extract_urls_from_search_results(source_str)

    # Get configuration
    configurable = Configuration.from_runnable_config(config)

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
        return Command(update={"completed_sections": [section], "all_urls": urls}, goto=END)
    else:
        return Command(
            update={"search_queries": feedback.follow_up_queries, "section": section, "all_urls": urls},
            goto="search_web",
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
            references += f"[{i}] {url}\n"
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

    system_instructions = deep_research_planner_instructions.format(
        topic=topic,
        section_name=section.name,
        section_content=section.content,
        current_depth=current_depth,
        breadth=breadth,
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

    # Get writer model
    writer_provider = get_config_value(configurable.writer_provider)
    writer_model_name = get_config_value(configurable.writer_model)
    writer_model_config = configurable.writer_model_config or {}
    writer_model = init_chat_model(model=writer_model_name, model_provider=writer_provider, **writer_model_config)

    queries_by_subtopic = {}
    # Generate queries for each subtopic
    for subtopic in subtopics:
        system_instructions = deep_research_queries_instructions.format(
            topic=topic,
            section_name=section.name,
            subtopic_name=subtopic.name,
            subtopic_description=subtopic.description,
            number_of_queries=number_of_queries,
        )
        system_instructions += f"\n\nPlease respond in **{configurable.language}** language."

        structured_llm = writer_model.with_structured_output(Queries)
        queries = structured_llm.invoke(
            [
                SystemMessage(content=system_instructions),
                HumanMessage(content="このサブトピックに関する検索クエリを生成してください。"),
            ]
        )
        queries_by_subtopic[subtopic.name] = queries.queries

    return {"deep_research_queries": queries_by_subtopic}


async def deep_research_search(state: SectionState, config: RunnableConfig):
    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    search_api = get_config_value(configurable.search_api)
    search_api_config = configurable.search_api_config or {}
    params_to_pass = get_search_params(search_api, search_api_config)
    queries_by_subtopic = state["deep_research_queries"]

    # Search the web for each subtopic
    results_by_subtopic = {}
    for subtopic_name, queries in queries_by_subtopic.items():
        query_list = [query.search_query for query in queries]

        subtopic_source_str = await select_and_execute_search(search_api, query_list, params_to_pass)
        results_by_subtopic[subtopic_name] = subtopic_source_str

    return {"deep_research_results": results_by_subtopic}


def deep_research_writer(state: SectionState, config: RunnableConfig):
    configurable = Configuration.from_runnable_config(config)
    max_depth = configurable.deep_research_depth

    topic = state["topic"]
    section = state["section"]
    current_depth = state["current_depth"]
    results_by_subtopic = state["deep_research_results"]

    # Extract URLs from deep research results
    urls = []
    for _, search_results in results_by_subtopic.items():
        urls.extend(extract_urls_from_search_results(search_results))

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
        return Command(
            update={"section": updated_section, "completed_sections": [updated_section], "all_urls": urls}, goto=END
        )
    else:
        return Command(
            update={"section": updated_section, "current_depth": current_depth, "all_urls": urls},
            goto="deep_research_planner",
        )


# Report section sub-graph --

# Add nodes
section_builder = StateGraph(SectionState, output=SectionOutputState)
section_builder.add_node("generate_queries", generate_queries)
section_builder.add_node("search_web", search_web)
section_builder.add_node("write_section", write_section)

section_builder.add_node("deep_research_planner", deep_research_planner)
section_builder.add_node("generate_deep_research_queries", generate_deep_research_queries)
section_builder.add_node("deep_research_search", deep_research_search)
section_builder.add_node("deep_research_writer", deep_research_writer)

section_builder.add_edge(START, "generate_queries")
section_builder.add_edge("generate_queries", "search_web")
section_builder.add_edge("search_web", "write_section")


def should_deep_research(state: SectionState) -> str:
    """深掘り調査を行うかどうかを決定する関数"""
    configurable = Configuration.from_runnable_config(state.get("config", {}))
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
builder.add_node("determine_if_question", determine_if_question)
builder.add_node("generate_introduction", generate_introduction)
builder.add_node("generate_report_plan", generate_report_plan)
builder.add_node("human_feedback", human_feedback)
builder.add_node("build_section_with_web_research", section_builder.compile())
builder.add_node("gather_completed_sections", gather_completed_sections)
builder.add_node("compile_final_report", compile_final_report)
builder.add_node("generate_conclusion", generate_conclusion)


# Add edges
builder.add_edge(START, "determine_if_question")
builder.add_edge("determine_if_question", "generate_introduction")
builder.add_edge("generate_introduction", "generate_report_plan")
builder.add_edge("generate_report_plan", "human_feedback")
builder.add_edge("build_section_with_web_research", "gather_completed_sections")
builder.add_edge("gather_completed_sections", "generate_conclusion")
builder.add_edge("generate_conclusion", "compile_final_report")
builder.add_edge("compile_final_report", END)

graph = builder.compile()
