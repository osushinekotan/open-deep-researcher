import apiClient from '@/lib/api';
import { FeedbackRequest, FeedbackResponse } from '@/types/api';

export const feedbackService = {
  // フィードバックを提出
  submitFeedback: async (request: FeedbackRequest): Promise<FeedbackResponse> => {
    const response = await apiClient.post('/feedback/submit', request);
    return response.data;
  },
};