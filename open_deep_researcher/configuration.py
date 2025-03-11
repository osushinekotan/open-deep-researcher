import os
from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Any

from langchain_core.runnables import RunnableConfig

# NOTE: introduction & conclusion are considered outside of the main body
DEFAULT_REPORT_STRUCTURE = """Use this structure to create a report on the user-provided topic:
Main Body Sections:
   - Each section should focus on a sub-topic of the user-provided topic
   - if user provided question, you should make critical sections to answer the question
   - Do not include introduction or conclusion
"""


class SearchSource(Enum):
    WEB = "web"
    LOCAL = "local"
    HYBRID = "hybrid"


class PlannerProvider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GROQ = "groq"


class WriterProvider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GROQ = "groq"


class SearchProvider(Enum):
    TAVILY = "tavily"
    ARXIV = "arxiv"
    PUBMED = "pubmed"
    EXA = "exa"
    LOCAL = "local"
    GOOGLE_PATENT = "google_patent"


@dataclass(kw_only=True)
class Configuration:
    """The configurable fields for the chatbot."""

    report_structure: str = DEFAULT_REPORT_STRUCTURE  # Defaults to the default report structure
    number_of_queries: int = 2  # Number of search queries to generate per iteration
    max_reflection: int = 2  # Maximum number of reflection + search iterations

    max_section_words: int = 2048  # セクション（main body）の最大単語数
    max_subsection_words: int = 2048  # サブセクションの最大単語数
    max_introduction_words: int = 2048  # イントロダクションの最大単語数
    max_conclusion_words: int = 2048  # 結論の最大単語数

    enable_deep_research: bool = True
    deep_research_depth: int = 1
    deep_research_breadth: int = 2

    skip_human_feedback: bool = False

    planner_provider: PlannerProvider = PlannerProvider.OPENAI
    planner_model: str = "gpt-4o"
    planner_model_config: dict[str, Any] | None = field(
        default_factory=lambda: {
            "max_tokens": 8192,
            "temperature": 0.0,
        }
    )

    writer_provider: WriterProvider = WriterProvider.OPENAI
    writer_model: str = "gpt-4o"
    writer_model_config: dict[str, Any] | None = field(
        default_factory=lambda: {
            "max_tokens": 8192,
            "temperature": 0.0,
        }
    )

    conclusion_writer_provider: WriterProvider = WriterProvider.OPENAI
    conclusion_writer_model: str = "o3-mini"
    conclusion_writer_model_config: dict[str, Any] | None = field(
        default_factory=lambda: {
            "max_tokens": 8192,
        }
    )

    max_tokens_per_source = 8192  # 検索結果の最大トークン数
    introduction_search_provider: SearchProvider = SearchProvider.TAVILY
    planning_search_provider: SearchProvider = SearchProvider.TAVILY
    # 検索時に利用可能なプロバイダーのリストを指定 (human feedback で確定させる)
    available_search_providers: list[SearchProvider] = field(
        default_factory=lambda: [
            SearchProvider.TAVILY,
            # SearchProvider.ARXIV,
            # SearchProvider.PUBMED,
            # SearchProvider.EXA,
            # SearchProvider.LOCAL,
            # SearchProvider.GOOGLE_PATEN
        ]
    )
    # deep_research 時に利用するプロバイダーのリストを指定
    deep_research_providers: list[SearchProvider] = field(default_factory=lambda: [SearchProvider.TAVILY])
    default_search_provider = (
        SearchProvider.TAVILY
    )  # デフォルトの検索プロバイダー (report plan で provider が指定されていない場合に利用)

    tavily_search_config: dict[str, Any] | None = field(
        default_factory=lambda: {
            "max_results": 5,
            "include_raw_content": False,
        }
    )
    arxiv_search_config: dict[str, Any] | None = field(
        default_factory=lambda: {
            "load_max_docs": 5,
            "get_full_documents": True,
            "load_all_available_meta": True,
            "add_aditional_metadata": True,
        }
    )
    local_search_config: dict[str, Any] | None = field(
        default_factory=lambda: {
            "vector_store_path": "data/vector_store",
            "local_document_path": None,
            "embedding_provider": "openai",
            "embedding_model": "text-embedding-3-small",
        }
    )
    google_patent_search_config: dict[str, Any] | None = field(
        default_factory=lambda: {
            "db_path": "data/patent_database.sqlite",
            "limit": 10,
        }
    )

    language: str = "japanese"

    @classmethod
    def from_runnable_config(cls, config: RunnableConfig | None = None) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = config["configurable"] if config and "configurable" in config else {}
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name)) for f in fields(cls) if f.init
        }
        return cls(**{k: v for k, v in values.items() if v})
