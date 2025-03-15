// APIレスポンスの型定義
export interface ResearchResponse {
  research_id: string;
  topic: string;
  status: string;
  message: string;
}

export interface SectionModel {
  name: string;
  description: string;
  content?: string;
  search_options?: any;
}

export interface ResearchStatus {
  research_id: string;
  status: string;
  topic: string;
  sections?: SectionModel[];
  progress?: number;
  completed_sections?: string[];
  final_report?: string;
  error?: string;
  completed_at?: string; // 完了日時フィールドを追加
}

export interface PlanResponse {
  research_id: string;
  sections: SectionModel[];
  waiting_for_feedback: boolean;
}

export interface FeedbackResponse {
  message: string;
}

export interface ResearchResult {
  research_id: string;
  status: string;
  final_report: string;
  completed_at: string;
}

export enum SearchProviderEnum {
  TAVILY = "tavily",
  ARXIV = "arxiv",
  LOCAL = "local",
}

export enum PlannerProviderEnum {
  ANTHROPIC = "anthropic",
  OPENAI = "openai",
  GROQ = "groq"
}

export enum WriterProviderEnum {
  ANTHROPIC = "anthropic",
  OPENAI = "openai",
  GROQ = "groq"
}

// Tavilyの検索設定インターフェース
export interface TavilySearchConfig {
  max_results: number;
  include_raw_content: boolean;
}

// arXivの検索設定インターフェース
export interface ArxivSearchConfig {
  load_max_docs: number;
  get_full_documents: boolean;
}

// ローカル検索の設定インターフェース
export interface LocalSearchConfig {
  local_document_path: string;
  chunk_size: number;
  chunk_overlap: number;
}

export interface ResearchConfig {
  report_structure?: string;
  number_of_queries?: number;
  max_reflection?: number;
  max_sections?: number;
  request_delay?: number;
  max_section_words?: number;
  max_subsection_words?: number;
  max_introduction_words?: number;
  max_conclusion_words?: number;
  enable_deep_research?: boolean;
  deep_research_depth?: number;
  deep_research_breadth?: number;
  skip_human_feedback?: boolean;
  planner_provider?: PlannerProviderEnum;
  planner_model?: string;
  planner_model_config?: Record<string, any>;
  writer_provider?: WriterProviderEnum;
  writer_model?: string;
  writer_model_config?: Record<string, any>;
  conclusion_writer_provider?: WriterProviderEnum;
  conclusion_writer_model?: string;
  conclusion_writer_model_config?: Record<string, any>;
  introduction_search_provider?: SearchProviderEnum;
  planning_search_provider?: SearchProviderEnum;
  available_search_providers?: SearchProviderEnum[];
  deep_research_providers?: SearchProviderEnum[];
  default_search_provider?: SearchProviderEnum;
  max_tokens_per_source?: number;
  tavily_search_config?: TavilySearchConfig;
  arxiv_search_config?: ArxivSearchConfig;
  local_search_config?: LocalSearchConfig;
  language?: string;
}

export interface ResearchRequest {
  topic: string;
  config?: ResearchConfig;
}

export interface FeedbackRequest {
  research_id: string;
  feedback?: string;
}