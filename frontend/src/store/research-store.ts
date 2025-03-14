import { create } from 'zustand';
import { ResearchConfig, PlannerProviderEnum, WriterProviderEnum, SearchProviderEnum } from '@/types/api';

interface ResearchState {
  // 新規リサーチ作成用の状態
  topic: string;
  config: ResearchConfig;
  
  // アクション
  setTopic: (topic: string) => void;
  updateConfig: (config: Partial<ResearchConfig>) => void;
  resetForm: () => void;
}

// デフォルト設定
const defaultConfig: ResearchConfig = {
  // 基本設定
  report_structure: undefined,
  number_of_queries: 2,
  max_reflection: 2,
  max_sections: 5,
  request_delay: 1.0,
  
  // 単語数制限
  max_section_words: 1000,
  max_subsection_words: 500,
  max_introduction_words: 500,
  max_conclusion_words: 500,
  
  // 深掘り調査設定
  enable_deep_research: true,
  deep_research_depth: 1,
  deep_research_breadth: 2,
  
  // フィードバック設定
  skip_human_feedback: false,
  
  // モデル設定
  planner_provider: PlannerProviderEnum.OPENAI,
  planner_model: 'gpt-4o',
  planner_model_config: {
    max_tokens: 4096
  },
  
  writer_provider: WriterProviderEnum.OPENAI,
  writer_model: 'gpt-4o-mini',
  writer_model_config: {
    max_tokens: 8192
  },
  
  conclusion_writer_provider: WriterProviderEnum.OPENAI,
  conclusion_writer_model: 'gpt-4o-mini',
  conclusion_writer_model_config: {
    max_tokens: 2048
  },
  
  // 検索プロバイダー設定
  introduction_search_provider: SearchProviderEnum.TAVILY,
  planning_search_provider: SearchProviderEnum.TAVILY,
  available_search_providers: [SearchProviderEnum.TAVILY],
  deep_research_providers: [SearchProviderEnum.TAVILY],
  default_search_provider: SearchProviderEnum.TAVILY,
  
  // トークン数制限
  max_tokens_per_source: 8192,
  
  // プロバイダー別の設定
  tavily_search_config: {
    max_results: 5,
    include_raw_content: false,
  },
  arxiv_search_config: {
    load_max_docs: 5,
    get_full_documents: true,
  },
  local_search_config: {
    local_document_path: "",
    chunk_size: 10000,
    chunk_overlap: 2000,
  },
  
  // 言語設定
  language: 'japanese',
};

export const useResearchStore = create<ResearchState>((set) => ({
  topic: '',
  config: { ...defaultConfig },
  
  setTopic: (topic) => set({ topic }),
  
  updateConfig: (partialConfig) => set((state) => ({ 
    config: { ...state.config, ...partialConfig } 
  })),
  
  resetForm: () => set({ topic: '', config: { ...defaultConfig } }),
}));