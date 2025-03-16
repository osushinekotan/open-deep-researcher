import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface AuthState {
  isAuthenticated: boolean;
  username: string | null;
  hydrated: boolean; // 永続化データのロード完了フラグ
  
  login: (username: string) => void;
  logout: () => void;
  setHydrated: (state: boolean) => void; // ハイドレーション状態セッター
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      username: null,
      hydrated: false,
      
      login: (username) => {
        console.log(`ログイン: ${username}`);
        set({ isAuthenticated: true, username });
      },
      
      logout: () => {
        console.log('ログアウト実行');
        set({ isAuthenticated: false, username: null });
      },
      
      setHydrated: (state) => {
        set({ hydrated: state });
      }
    }),
    {
      name: 'auth-storage', // localStorage のキー
      storage: createJSONStorage(() => localStorage),
      onRehydrateStorage: () => (state) => {
        // ハイドレーション完了時に呼ばれる
        if (state) {
          state.setHydrated(true);
          console.log('認証状態復元完了:', state.isAuthenticated, state.username);
        }
      }
    }
  )
);

// 認証状態のハイドレーションを確認するフック
export const useAuthHydration = () => {
  const hydrated = useAuthStore((state) => state.hydrated);
  return hydrated;
};