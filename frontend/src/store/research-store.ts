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
  number_of_queries: 2,
  max_reflection: 2,
  enable_deep_research: true,
  deep_research_depth: 1,
  deep_research_breadth: 2,
  skip_human_feedback: false,
  planner_provider: PlannerProviderEnum.OPENAI,
  planner_model: 'gpt-4o',
  writer_provider: WriterProviderEnum.OPENAI,
  writer_model: 'gpt-4o',
  available_search_providers: [SearchProviderEnum.TAVILY],
  deep_research_providers: [SearchProviderEnum.TAVILY],
  default_search_provider: SearchProviderEnum.TAVILY,
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