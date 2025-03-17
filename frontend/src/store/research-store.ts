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
  number_of_queries: 5,
  max_reflection: 2,
  max_sections: 5,
  request_delay: 1.0,
  
  // 単語数制限
  max_section_words: 5000,
  max_subsection_words: 5000,
  max_introduction_words: 5000,
  max_conclusion_words: 5000,
  
  // 深掘り調査設定
  enable_deep_research: true,
  deep_research_depth: 1,
  deep_research_breadth: 2,
  
  // フィードバック設定
  skip_human_feedback: true,
  
  // モデル設定
  planner_provider: PlannerProviderEnum.OPENAI,
  planner_model: 'gpt-4o',
  planner_model_config: {
    max_tokens: 8192
  },
  
  writer_provider: WriterProviderEnum.OPENAI,
  writer_model: 'gpt-4o',
  writer_model_config: {
    max_tokens: 8192
  },
  
  conclusion_writer_provider: WriterProviderEnum.OPENAI,
  conclusion_writer_model: 'gpt-4o',
  conclusion_writer_model_config: {
    max_tokens: 8192
  },
  
  // 検索プロバイダー設定
  introduction_search_provider: SearchProviderEnum.TAVILY,
  planning_search_provider: SearchProviderEnum.TAVILY,
  available_search_providers: [SearchProviderEnum.TAVILY],
  deep_research_providers: [SearchProviderEnum.TAVILY],
  default_search_provider: SearchProviderEnum.TAVILY,
  
  // トークン数制限
  max_tokens_per_source: 512,
  
  // プロバイダー別の設定
  tavily_search_config: {
    max_results: 5,
    include_raw_content: true,
  },
  arxiv_search_config: {
    load_max_docs: 5,
    get_full_documents: true,
  },
  local_search_config: {
    chunk_size: 10000,
    chunk_overlap: 2000,
    top_k: 5,
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