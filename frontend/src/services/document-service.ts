import apiClient from '@/lib/api';

// APIエンドポイント
const API_ENDPOINTS = {
  UPLOAD_DOCUMENTS: '/documents/upload',
  LIST_DOCUMENTS: '/documents/list',
  DELETE_DOCUMENT: (filename: string) => `/documents/${filename}`,
  TOGGLE_DOCUMENT: (filename: string) => `/documents/${filename}/enable`,
};

export const documentService = {
  // ドキュメントをアップロード - ユーザーIDを追加
  uploadDocuments: async (files: File[], username?: string) => {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    
    // ユーザーIDをクエリパラメータとして追加
    const endpoint = username 
      ? `${API_ENDPOINTS.UPLOAD_DOCUMENTS}?user_id=${encodeURIComponent(username)}` 
      : API_ENDPOINTS.UPLOAD_DOCUMENTS;
    
    const response = await apiClient.post(endpoint, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  
  // ドキュメント一覧を取得 - ユーザーIDを追加
  listDocuments: async (username?: string) => {
    const endpoint = username 
      ? `${API_ENDPOINTS.LIST_DOCUMENTS}?user_id=${encodeURIComponent(username)}`
      : API_ENDPOINTS.LIST_DOCUMENTS;
    
    const response = await apiClient.get(endpoint);
    return response.data.documents;
  },
  
  // ドキュメントを削除 - ユーザーIDを追加
  deleteDocument: async (filename: string, username?: string) => {
    const endpoint = username 
      ? `${API_ENDPOINTS.DELETE_DOCUMENT(filename)}?user_id=${encodeURIComponent(username)}`
      : API_ENDPOINTS.DELETE_DOCUMENT(filename);
    
    const response = await apiClient.delete(endpoint);
    return response.data;
  },
  
  // ドキュメントの有効/無効を切り替え - ユーザーIDを追加
  toggleDocumentEnabled: async (filename: string, enable: boolean, username?: string) => {
    // enableパラメータをクエリパラメータとして追加
    let endpoint = `${API_ENDPOINTS.TOGGLE_DOCUMENT(filename)}?enable=${enable}`;
    
    // ユーザーIDもクエリパラメータとして追加（存在する場合）
    if (username) {
      endpoint += `&user_id=${encodeURIComponent(username)}`;
    }
    
    // リクエストボディは空にする（クエリパラメータを使用するため）
    const response = await apiClient.put(endpoint, {});
    return response.data;
  },
};