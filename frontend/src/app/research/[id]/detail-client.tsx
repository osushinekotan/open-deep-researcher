"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { StatusBadge } from "@/components/research/status-badge";
import { SectionList } from "@/components/research/section-list";
import { ArrowLeft, RefreshCw, ClipboardCopy } from "lucide-react";
import { formatDate, getStatusInfo } from "@/lib/utils";
import { useResearchStatus } from "@/hooks/use-research";

export function DetailClient({ researchId }: { researchId: string }) {
  const router = useRouter();
  
  const { 
    data: research, 
    isLoading, 
    error,
    refetch
  } = useResearchStatus(researchId);

  // レンダリング後にリダイレクトを行うためにuseEffectを使用
  useEffect(() => {
    if (research) {
      if (research.status === 'completed') {
        router.push(`/research/${researchId}/result`);
      } else if (research.status === 'waiting_for_feedback') {
        router.push(`/research/${researchId}/feedback`);
      }
    }
  }, [research, router, researchId]);

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
          <div className="flex justify-center gap-4">
            <Button variant="outline" onClick={() => router.push('/dashboard')}>
              ダッシュボードに戻る
            </Button>
            <Button onClick={() => refetch()}>
              再読み込み
            </Button>
          </div>
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

  // リダイレクト中のステータスの場合は、ローディング表示のままにする
  if (research.status === 'completed' || research.status === 'waiting_for_feedback') {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-4xl">
        <div className="text-center py-16">
          <p className="text-gray-600 mb-4">リダイレクト中...</p>
        </div>
      </div>
    );
  }

  const { status, topic, progress = 0, sections = [], completed_sections = [] } = research;
  const statusInfo = getStatusInfo(status);
  
  // 作成日（ダミー）
  const createdAt = new Date().toISOString();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-4xl">
      <div className="flex items-center gap-2 text-gray-600 mb-6 hover:text-gray-800 transition-colors">
        <Link href="/dashboard" className="flex items-center gap-2">
          <ArrowLeft size={16} />
          <span>ダッシュボードに戻る</span>
        </Link>
      </div>

      <div className="flex justify-between items-start mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold">リサーチ詳細</h1>
            <StatusBadge status={status} />
          </div>
          <p className="text-sm text-gray-500">作成日: {formatDate(createdAt)}</p>
        </div>
        <Button 
          variant="outline" 
          size="sm" 
          className="flex items-center gap-1"
          onClick={() => refetch()}
        >
          <RefreshCw size={14} />
          <span>更新</span>
        </Button>
      </div>

      <Card className="mb-8">
        <CardHeader className="pb-3">
          <CardTitle className="text-xl">リサーチトピック</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-start gap-2 p-4 bg-gray-50 rounded-md border relative group">
            <p className="text-lg text-gray-800">{topic}</p>
            <Button 
              variant="ghost" 
              size="icon" 
              className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
              title="コピー"
              onClick={() => {
                navigator.clipboard.writeText(topic);
              }}
            >
              <ClipboardCopy size={14} />
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="mb-8">
        <div className="flex justify-between mb-2">
          <h2 className="text-xl font-bold">進捗状況</h2>
          <span className={statusInfo.textColor + " font-semibold"}>{Math.round(progress * 100)}%</span>
        </div>
        <Progress value={progress * 100} className="h-2 mb-4" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>セクション</CardTitle>
          <p className="text-sm text-gray-500">
            リサーチプランのセクション一覧と進行状況
          </p>
        </CardHeader>
        <CardContent>
          {sections.length > 0 ? (
            <SectionList sections={sections} completedSections={completed_sections} />
          ) : (
            <div className="text-center py-6 bg-gray-50 rounded-md">
              <p className="text-gray-500">セクション情報はまだありません</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}