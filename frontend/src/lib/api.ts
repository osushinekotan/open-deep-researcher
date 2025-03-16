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
    // 成功レスポンスのログ（開発環境でのみ出力）
    if (process.env.NODE_ENV === 'development') {
      console.log(`API Response: ${response.status} for ${response.config.url}`);
    }
    return response;
  },
  (error) => {
    // エラー情報を安全に記録
    const errorInfo = {
      message: error.message || 'Unknown error',
      status: error.response?.status,
      statusText: error.response?.statusText,
      url: error.config?.url,
      method: error.config?.method?.toUpperCase()
    };
    
    // 開発環境でのみ詳細なエラーログを出力
    if (process.env.NODE_ENV === 'development') {
      // エラー情報を構造化して表示（オブジェクトの展開を避ける）
      console.log('API Error:', 
        `${errorInfo.status} ${errorInfo.statusText} - ${errorInfo.message} - ${errorInfo.method} ${errorInfo.url}`
      );
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;