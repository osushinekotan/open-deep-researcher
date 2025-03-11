import operator
from typing import Annotated, Literal, TypedDict

from pydantic import BaseModel, Field


class Section(BaseModel):
    name: str = Field(
        description="Name for this section of the report.",
    )
    description: str = Field(
        description="Brief overview of the main topics and concepts to be covered in this section.",
    )
    content: str = Field(description="The content of the section.")
    search_options: list[str] = Field(
        description="List of search providers to use for this section (e.g., tavily, arxiv, pubmed, exa, local, google_patent).",
    )


class Sections(BaseModel):
    sections: list[Section] = Field(
        description="Sections of the report.",
    )


class SearchQuery(BaseModel):
    search_query: str = Field(None, description="Query for web search.")


class Queries(BaseModel):
    queries: list[SearchQuery] = Field(
        description="List of search queries.",
    )


class Feedback(BaseModel):
    grade: Literal["pass", "fail"] = Field(
        description="Evaluation result indicating whether the response meets requirements ('pass') or needs revision ('fail')."
    )
    follow_up_queries: list[SearchQuery] = Field(
        description="List of follow-up search queries.",
    )


class ReportStateInput(TypedDict):
    topic: str  # Report topic


class ReportStateOutput(TypedDict):
    final_report: str  # Final report


class ReportState(TypedDict):
    topic: str  # Report topic
    is_question: bool  # Flag to indicate if topic is a question
    feedback_on_report_plan: str  # Feedback on the report plan
    sections: list[Section]  # List of report sections
    completed_sections: Annotated[list, operator.add]  # Send() API key
    report_sections_from_research: str  # String of any completed sections from research to write final sections
    introduction: str  # Introduction
    conclusion: str  # Conclusion
    final_report: str  # Final report
    all_urls: Annotated[list[str], operator.add]  # List of all URLs referenced
    local_documents_ready: bool  # Flag to indicate if local documents are ready
    patent_db_ready: bool  # Flag to indicate if patent database is ready


class SectionState(TypedDict):
    topic: str  # Report topic
    section: Section  # Report section
    search_iterations: int  # Number of search iterations done
    source_str: str  # String of formatted source content from web search

    search_results_by_provider: dict[str, str]  # 各プロバイダの検索結果
    search_queries_by_provider: dict[str, list[SearchQuery]]

    report_sections_from_research: str  # String of any completed sections from research to write final sections
    completed_sections: list[Section]  # Final key we duplicate in outer state for Send() API

    deep_research_topics: list  # 深掘りするトピックのリスト
    current_depth: int  # 現在の深掘りの深さ
    deep_research_queries: dict[str, list]  # 深掘り用の検索クエリ
    deep_research_results: dict[str, list]  # 深掘り検索の結果

    all_urls: Annotated[list[str], operator.add]  # List of all URLs referenced:


class SectionOutputState(TypedDict):
    completed_sections: list[Section]  # Final key we duplicate in outer state for Send() API
    all_urls: Annotated[list[str], operator.add]  # List of all URLs referenced


class SubTopic(BaseModel):
    name: str = Field(description="深掘りするサブトピックの名前")
    description: str = Field(description="このサブトピックが重要である理由と調査すべき具体的な側面")
    key_questions: list[str] = Field(description="このサブトピックについて回答すべき重要な質問のリスト")


class SubTopics(BaseModel):
    subtopics: list[SubTopic] = Field(description="深掘りするサブトピックのリスト")
