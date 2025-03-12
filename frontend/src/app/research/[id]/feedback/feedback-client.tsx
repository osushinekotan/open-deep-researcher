"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ThumbsUp } from "lucide-react";
import { formatDate } from "@/lib/utils";
import { useResearchStatus, useResearchPlan } from "@/hooks/use-research";
import { FeedbackForm } from "@/components/forms/feedback-form";
import { sampleResearchPlan } from "@/lib/utils";

export function FeedbackClient({ researchId }: { researchId: string }) {
  const router = useRouter();
  
  const { 
    data: research, 
    isLoading: statusLoading, 
    error: statusError 
  } = useResearchStatus(researchId);
  
  const { 
    data: plan, 
    isLoading: planLoading, 
    error: planError 
  } = useResearchPlan(researchId);

  const isLoading = statusLoading || planLoading;
  const error = statusError || planError;
  
  // useEffectを使用してリダイレクトの処理を行う
  useEffect(() => {
    if (research && research.status !== 'waiting_for_feedback') {
      router.push(`/research/${researchId}`);
    }
  }, [research, router, researchId]);

  // 作成日（ダミー）
  const createdAt = new Date().toISOString();

  // エラー時のハンドリング
  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-4xl">
        <div className="text-center py-16 bg-red-50 rounded-lg border border-red-100">
          <h2 className="text-2xl font-bold text-red-600 mb-4">エラーが発生しました</h2>
          <p className="text-gray-600 mb-6">リサーチの読み込み中にエラーが発生しました。</p>
          <pre className="text-left bg-red-100 p-4 rounded mx-auto max-w-lg mb-6 overflow-auto text-sm">
            {JSON.stringify(error, null, 2)}
          </pre>
          <Button variant="outline" onClick={() => router.push('/dashboard')}>
            ダッシュボードに戻る
          </Button>
        </div>
      </div>
    );
  }

  // ローディング時のスケルトン表示
  if (isLoading || !research) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-4xl">
        <div className="flex items-center gap-2 text-gray-600 mb-6 animate-pulse">
          <div className="h-4 w-24 bg-gray-200 rounded"></div>
        </div>
        <div className="h-8 w-64 bg-gray-200 rounded mb-2 animate-pulse"></div>
        <div className="h-4 w-40 bg-gray-200 rounded mb-8 animate-pulse"></div>
        <div className="h-48 bg-gray-100 rounded-lg animate-pulse mb-8"></div>
        <div className="h-64 bg-gray-100 rounded-lg animate-pulse"></div>
      </div>
    );
  }

  // フィードバック待ち状態でない場合はリダイレクト中の表示
  if (research.status !== 'waiting_for_feedback') {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-4xl">
        <div className="text-center py-16">
          <p className="text-gray-600 mb-4">リダイレクト中...</p>
        </div>
      </div>
    );
  }

  // プランがない場合はサンプルデータを使用（開発時のみ）
  const sections = plan?.sections || sampleResearchPlan.sections;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-4xl">
      <div className="flex items-center gap-2 text-gray-600 mb-6 hover:text-gray-800 transition-colors">
        <Link href={`/research/${researchId}`} className="flex items-center gap-2">
          <ArrowLeft size={16} />
          <span>リサーチ詳細に戻る</span>
        </Link>
      </div>

      <div className="flex items-center gap-3 mb-2">
        <h1 className="text-2xl font-bold">リサーチフィードバック</h1>
      </div>
      <p className="text-sm text-gray-500 mb-6">作成日: {formatDate(createdAt)}</p>

      <Card className="mb-8 border-yellow-200 bg-yellow-50">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg text-yellow-800 flex items-center gap-2">
            <ThumbsUp size={18} />
            フィードバックが必要です
          </CardTitle>
          <CardDescription className="text-yellow-700">
            リサーチプランを確認し、フィードバックを提供するか承認してください
          </CardDescription>
        </CardHeader>
        <CardContent>
          <FeedbackForm researchId={researchId} sections={sections} />
        </CardContent>
      </Card>
    </div>
  );
}