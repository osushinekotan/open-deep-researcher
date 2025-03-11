import apiClient from '@/lib/api';
import { 
  ResearchRequest, 
  ResearchResponse, 
  ResearchStatus, 
  PlanResponse, 
  ResearchResult
} from '@/types/api';

// バックエンドAPIエンドポイントを明示的に定義（正しいパス形式に統一）
const API_ENDPOINTS = {
  START_RESEARCH: '/research/start',
  LIST_RESEARCHES: '/research/list',
  GET_RESEARCH_STATUS: (id: string) => `/research/${id}/status`,
  GET_RESEARCH_PLAN: (id: string) => `/research/${id}/plan`,
  GET_RESEARCH_RESULT: (id: string) => `/research/${id}/result`,
  SUBMIT_FEEDBACK: '/feedback/submit',
};

export const researchService = {
  // 新しいリサーチを開始
  startResearch: async (request: ResearchRequest): Promise<ResearchResponse> => {
    console.log('リサーチ開始リクエスト:', request);
    const response = await apiClient.post(API_ENDPOINTS.START_RESEARCH, request);
    return response.data;
  },

  // リサーチのステータスを取得
  getResearchStatus: async (researchId: string): Promise<ResearchStatus> => {
    const endpoint = API_ENDPOINTS.GET_RESEARCH_STATUS(researchId);
    console.log(`ステータス取得: ${endpoint}`);
    try {
      const response = await apiClient.get(endpoint);
      console.log('ステータス取得成功:', response.status);
      return response.data;
    } catch (error) {
      console.error('ステータス取得エラー:', error);
      throw error;
    }
  },

  // リサーチプランを取得
  getResearchPlan: async (researchId: string): Promise<PlanResponse> => {
    const endpoint = API_ENDPOINTS.GET_RESEARCH_PLAN(researchId);
    console.log(`プラン取得: ${endpoint}`);
    try {
      const response = await apiClient.get(endpoint);
      console.log('プラン取得成功:', response.status);
      return response.data;
    } catch (error) {
      console.error('プラン取得エラー:', error);
      throw error;
    }
  },

  // リサーチ結果を取得
  getResearchResult: async (researchId: string): Promise<ResearchResult> => {
    const endpoint = API_ENDPOINTS.GET_RESEARCH_RESULT(researchId);
    console.log(`結果取得: ${endpoint}`);
    try {
      const response = await apiClient.get(endpoint);
      console.log('結果取得成功:', response.status);
      return response.data;
    } catch (error) {
      console.error('結果取得エラー:', error);
      throw error;
    }
  },

  // すべてのリサーチを取得
  listResearches: async (): Promise<ResearchStatus[]> => {
    console.log('リサーチ一覧取得');
    const response = await apiClient.get(API_ENDPOINTS.LIST_RESEARCHES);
    return response.data;
  },
};