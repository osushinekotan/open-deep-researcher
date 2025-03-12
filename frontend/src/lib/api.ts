import axios from 'axios';

// APIクライアントのベース設定
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // タイムアウトを10秒に設定
});

// デバッグ用リクエストインターセプター
apiClient.interceptors.request.use(
  (config) => {
    // 完全なURLを表示（デバッグ用）
    const fullUrl = `${config.baseURL}${config.url}`;
    console.log(`API Request: ${config.method?.toUpperCase()} ${fullUrl}`);
    return config;
  },
  (error) => {
    console.error('Request Error:', error);
    return Promise.reject(error);
  }
);

// レスポンスインターセプター
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} for ${response.config.url}`);
    return response;
  },
  (error) => {
    // エラー情報をより詳細に記録
    console.error('API Error:', {
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      url: error.config?.url,
      fullUrl: error.config?.baseURL + error.config?.url,
      method: error.config?.method?.toUpperCase()
    });
    return Promise.reject(error);
  }
);

export default apiClient;