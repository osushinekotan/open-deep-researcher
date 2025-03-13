from enum import Enum
from typing import Any

from pydantic import BaseModel

from app.config import DOCUMENTS_DIR, FTS_DATABASE, VECTOR_STORE_DIR

DEFAULT_REPORT_STRUCTURE = """Use this structure to create a report on the user-provided topic:
Main Body Sections:
   - Each section should focus on a sub-topic of the user-provided topic
   - if user provided question, you should make critical sections to answer the question
   - Do not include introduction or conclusion
"""


class PlannerProviderEnum(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GROQ = "groq"


class WriterProviderEnum(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GROQ = "groq"


class SearchProviderEnum(str, Enum):
    TAVILY = "tavily"
    ARXIV = "arxiv"
    PUBMED = "pubmed"
    EXA = "exa"
    LOCAL = "local"
    GOOGLE_PATENT = "google_patent"


class ResearchConfig(BaseModel):
    # レポート構造と基本設定
    report_structure: str | None = DEFAULT_REPORT_STRUCTURE
    number_of_queries: int = 2
    max_reflection: int = 2
    request_delay: float = 0.0

    # 単語数制限
    max_section_words: int = 1000
    max_subsection_words: int = 500
    max_introduction_words: int = 500
    max_conclusion_words: int = 500

    # 深掘り調査設定
    enable_deep_research: bool = True
    deep_research_depth: int = 1
    deep_research_breadth: int = 2

    # フィードバック設定
    skip_human_feedback: bool = False

    # モデル設定
    planner_provider: PlannerProviderEnum = PlannerProviderEnum.OPENAI
    planner_model: str = "gpt-4o-mini"
    planner_model_config: dict[str, Any] | None = None

    writer_provider: WriterProviderEnum = WriterProviderEnum.OPENAI
    writer_model: str = "gpt-4o-mini"
    writer_model_config: dict[str, Any] | None = None

    conclusion_writer_provider: WriterProviderEnum = WriterProviderEnum.OPENAI
    conclusion_writer_model: str = "gpt-4o-mini"
    conclusion_writer_model_config: dict[str, Any] | None = None

    # 検索プロバイダー設定
    introduction_search_provider: SearchProviderEnum = SearchProviderEnum.TAVILY
    planning_search_provider: SearchProviderEnum = SearchProviderEnum.TAVILY
    available_search_providers: list[SearchProviderEnum] = [SearchProviderEnum.TAVILY]
    deep_research_providers: list[SearchProviderEnum] = [SearchProviderEnum.TAVILY]
    default_search_provider: SearchProviderEnum = SearchProviderEnum.TAVILY

    # トークン数制限
    max_tokens_per_source: int = 8192

    # 検索プロバイダー別の設定
    tavily_search_config: dict[str, Any] | None = {
        "max_results": 5,
        "include_raw_content": False,
    }
    arxiv_search_config: dict[str, Any] | None = {
        "load_max_docs": 5,
        "get_full_documents": True,
    }
    local_search_config: dict[str, Any] | None = {
        "vector_store_path": str(VECTOR_STORE_DIR),
        "local_document_path": str(DOCUMENTS_DIR),
        "embedding_provider": "openai",
        "embedding_model": "text-embedding-3-small",
    }
    google_patent_search_config: dict[str, Any] | None = {
        "db_path": str(FTS_DATABASE),
        "limit": 10,
        "query_expansion": True,
        "initial_document_limit": 1000,
    }

    # 言語設定
    language: str = "japanese"


class ResearchRequest(BaseModel):
    topic: str
    config: ResearchConfig | None = None


class ResearchResponse(BaseModel):
    research_id: str
    topic: str
    status: str = "pending"
    message: str = "Research task created"


class SectionModel(BaseModel):
    name: str
    description: str
    content: str | None = None
    search_options: list | None = None


class PlanResponse(BaseModel):
    research_id: str
    sections: list[SectionModel]
    waiting_for_feedback: bool = True


class FeedbackRequest(BaseModel):
    research_id: str
    feedback: str | None = None


class ResearchStatus(BaseModel):
    research_id: str
    status: str
    topic: str
    sections: list[SectionModel] | None = None
    progress: float | None = None
    completed_sections: list[str] | None = None
    final_report: str | None = None
    error: str | None = None
    completed_at: str | None = None
