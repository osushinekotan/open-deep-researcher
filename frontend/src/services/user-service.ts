import apiClient from '@/lib/api';
import { LoginRequest, LoginResponse, UserResponse } from '@/types/api';

export const userService = {
  // ユーザーログイン
  login: async (username: string): Promise<LoginResponse> => {
    const request: LoginRequest = { username };
    const response = await apiClient.post('/users/login', request);
    return response.data;
  },

  // ユーザー情報取得
  getUserInfo: async (username: string): Promise<UserResponse> => {
    const response = await apiClient.get(`/users/${username}`);
    return response.data;
  },

  // ユーザーのリサーチ一覧取得
  getUserResearches: async (username: string): Promise<any[]> => {
    const response = await apiClient.get(`/users/${username}/researches`);
    return response.data;
  },

  // ユーザーのドキュメント一覧取得
  getUserDocuments: async (username: string): Promise<any[]> => {
    const response = await apiClient.get(`/users/${username}/documents`);
    return response.data;
  },
};