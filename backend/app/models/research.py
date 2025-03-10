from enum import Enum
from typing import Any

from pydantic import BaseModel

DEFAULT_REPORT_STRUCTURE = """Use this structure to create a report on the user-provided topic:
Main Body Sections:
   - Each section should focus on a sub-topic of the user-provided topic
   - if user provided question, you should make critical sections to answer the question
   - Do not include introduction or conclusion
"""



class SearchSourceEnum(str, Enum):
    WEB = "web"
    LOCAL = "local"
    HYBRID = "hybrid"


class PlannerProviderEnum(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GROQ = "groq"


class WriterProviderEnum(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GROQ = "groq"


class ResearchConfig(BaseModel):
    report_structure: str | None = DEFAULT_REPORT_STRUCTURE
    number_of_queries: int = 2
    max_reflection: int = 2
    max_section_words: int = 1000
    max_subsection_words: int = 500
    max_introduction_words: int = 500
    max_conclusion_words: int = 500
    enable_deep_research: bool = True
    deep_research_depth: int = 1
    deep_research_breadth: int = 2
    skip_human_feedback: bool = False  # APIではデフォルトでfalseに設定
    planner_provider: PlannerProviderEnum = PlannerProviderEnum.OPENAI
    planner_model: str = "gpt-4o"
    planner_model_config: dict[str, Any] | None = None
    writer_provider: WriterProviderEnum = WriterProviderEnum.OPENAI
    writer_model: str = "gpt-4o"
    writer_model_config: dict[str, Any] | None = None
    conclusion_writer_provider: WriterProviderEnum = WriterProviderEnum.OPENAI
    conclusion_writer_model: str = "o3-mini"
    conclusion_writer_model_config: dict[str, Any] | None = None
    search_source: SearchSourceEnum = SearchSourceEnum.WEB
    web_search_config: dict[str, Any] | None = None
    local_search_config: dict[str, Any] | None = None
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
