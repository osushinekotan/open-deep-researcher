import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { researchService } from '@/services/research-service';
import { ResearchRequest } from '@/types/api';
import { useAuthStore } from '@/store/auth-store';

export const useResearchList = () => {
  const { isAuthenticated, username } = useAuthStore();
  
  return useQuery({
    queryKey: ['researches', username],
    queryFn: () => {
      console.log(`Fetching researches for user: ${username}`);
      if (isAuthenticated && username) {
        return researchService.getUserResearches(username);
      }
      return researchService.listResearches();
    },
    refetchInterval: 30000, // 30秒ごとに自動更新
  });
};


export const useResearchStatus = (researchId: string) => {
  return useQuery({
    queryKey: ['research', researchId, 'status'],
    queryFn: () => researchService.getResearchStatus(researchId),
    refetchInterval: (data) => {
      // 完了またはエラー状態、またはフィードバック待ちの場合はポーリングを停止
      if (
        data?.status === 'completed' || 
        data?.status === 'error' || 
        data?.status === 'waiting_for_feedback'
      ) {
        return false;
      }
      // それ以外は5秒ごとにポーリング
      return 5000;
    },
  });
};

export const useResearchPlan = (researchId: string) => {
  return useQuery({
    queryKey: ['research', researchId, 'plan'],
    queryFn: () => researchService.getResearchPlan(researchId),
    // プランがフィードバック待ちでない場合はキャッシュを使用
    staleTime: Infinity,
    retry: false,
    // プランがない場合はエラーを表示しない
    onError: () => {},
  });
};

export const useResearchResult = (researchId: string) => {
  return useQuery({
    queryKey: ['research', researchId, 'result'],
    queryFn: () => researchService.getResearchResult(researchId),
    // 結果は変わらないのでキャッシュを使用
    staleTime: Infinity,
    retry: false,
    // 結果がまだない場合はエラーを表示しない
    onError: () => {},
  });
};

export const useStartResearch = () => {
  const queryClient = useQueryClient();
  const { isAuthenticated, username } = useAuthStore();
  
  return useMutation({
    mutationFn: (request: ResearchRequest) => {
      // ログイン中の場合はユーザーIDを設定
      if (isAuthenticated && username) {
        return researchService.startResearch({
          ...request,
          user_id: username
        });
      }
      return researchService.startResearch(request);
    },
    onSuccess: () => {
      // リサーチリストを更新
      queryClient.invalidateQueries({ queryKey: ['researches'] });
    },
  });
};

export const useDeleteResearch = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (researchId: string) => researchService.deleteResearch(researchId),
    onSuccess: () => {
      // リサーチリストを更新
      queryClient.invalidateQueries({ queryKey: ['researches'] });
    },
  });
};