import { useMutation, useQueryClient } from '@tanstack/react-query';
import { feedbackService } from '@/services/feedback-service';
import { FeedbackRequest } from '@/types/api';

export const useSubmitFeedback = (researchId: string) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (feedback: string | undefined) => 
      feedbackService.submitFeedback({ research_id: researchId, feedback }),
    onSuccess: () => {
      // ステータスとプランを更新
      queryClient.invalidateQueries({ queryKey: ['research', researchId, 'status'] });
      queryClient.invalidateQueries({ queryKey: ['research', researchId, 'plan'] });
    },
  });
};