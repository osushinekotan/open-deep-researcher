"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore, useAuthHydration } from "@/store/auth-store";
import { Loader2 } from "lucide-react";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const router = useRouter();
  const { isAuthenticated, username } = useAuthStore();
  const hydrated = useAuthHydration(); // ハイドレーション状態を取得
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // ハイドレーションが完了するまで待機
    if (!hydrated) {
      return; // まだハイドレーションが完了していない
    }

    // ハイドレーション完了後に認証チェック
    if (!isAuthenticated) {
      console.log("未認証状態を検出 - ログインページにリダイレクト");
      router.push('/login');
    } else {
      console.log(`認証済みユーザー: ${username}`);
      setIsLoading(false);
    }
  }, [hydrated, isAuthenticated, username, router]);

  if (!hydrated || isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh]">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600 mb-4" />
        <p className="text-gray-600">
          {!hydrated ? "認証情報をロード中..." : "認証情報を確認中..."}
        </p>
      </div>
    );
  }

  return <>{children}</>;
}