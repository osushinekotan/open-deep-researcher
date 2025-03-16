"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ResearchForm } from "@/components/forms/research-form";
import { useAuthStore } from "@/store/auth-store";
import { Loader2 } from "lucide-react";
import { ProtectedRoute } from "@/components/protected-route";

export default function NewResearchPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [isRedirecting, setIsRedirecting] = useState(false);
  
  // 認証チェック - 未ログインならログインページへリダイレクト
  useEffect(() => {
    if (!isAuthenticated && !isRedirecting) {
      console.log("未認証ユーザーが新規リサーチページにアクセスしました - リダイレクトします");
      setIsRedirecting(true);
      router.push('/login');
    }
  }, [isAuthenticated, router, isRedirecting]);
  
  // リダイレクト中または未認証の場合はローディング表示
  if (!isAuthenticated || isRedirecting) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh]">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600 mb-4" />
        <p className="text-gray-600">リダイレクト中...</p>
      </div>
    );
  }

  return (
    <ProtectedRoute>
      <div className="container mx-auto px-4 py-8 max-w-3xl">
        <h1 className="text-3xl font-bold mb-2">Research</h1>
        <p className="text-gray-500 mb-8">リサーチトピックと設定をカスタマイズします</p>

        <ResearchForm />
      </div>
    </ProtectedRoute>
  );
}