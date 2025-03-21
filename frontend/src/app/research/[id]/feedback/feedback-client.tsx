"use client";

import React, { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ThumbsUp, Loader2 } from "lucide-react";
import { formatDate } from "@/lib/utils";
import { useResearchStatus, useResearchPlan } from "@/hooks/use-research";
import { FeedbackForm } from "@/components/forms/feedback-form";
import { sampleResearchPlan } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { researchService } from "@/services/research-service";

export function FeedbackClient({ researchId }: { researchId: string }) {
  const router = useRouter();
  const [waitingForUpdatedPlan, setWaitingForUpdatedPlan] = useState(false);
  // 元のプランのセクション内容を保持する参照
  const originalPlanRef = useRef<string | null>(null);
  // 新しいプランが検出されたかのフラグ
  const [newPlanDetected, setNewPlanDetected] = useState(false);
  
  const { 
    data: research, 
    isLoading: statusLoading, 
    error: statusError,
    refetch: refetchStatus 
  } = useResearchStatus(researchId);
  
  const { 
    data: plan, 
    isLoading: planLoading, 
    error: planError,
    refetch: refetchPlan 
  } = useQuery({
    queryKey: ['research', researchId, 'plan'],
    queryFn: () => researchService.getResearchPlan(researchId),
    refetchInterval: waitingForUpdatedPlan && !newPlanDetected ? 5000 : false,
    retry: false,
    onError: () => {},
  });

  const isLoading = statusLoading || planLoading;
  const error = statusError || planError;
  
  // フィードバック送信後のハンドラー
  const handleFeedbackSubmitted = () => {
    // オリジナルのプラン内容を保存
    if (plan && plan.sections) {
      // 簡易的なハッシュとしてセクション名と説明をJSONにして保存
      const planHash = JSON.stringify(plan.sections.map(s => ({ name: s.name, description: s.description })));
      originalPlanRef.current = planHash;
      console.log("元のプラン内容を保存:", planHash);
    }
    
    setWaitingForUpdatedPlan(true);
    setNewPlanDetected(false);
  };

  // 新しいプランを検出する
  useEffect(() => {
    if (!waitingForUpdatedPlan || !plan || !plan.sections || !originalPlanRef.current) return;
    
    // 現在のプランのハッシュを計算
    const currentPlanHash = JSON.stringify(plan.sections.map(s => ({ name: s.name, description: s.description })));
    
    // 元のプランと比較して変更があれば新プラン検出とする
    if (currentPlanHash !== originalPlanRef.current) {
      console.log("新しいプランを検出しました");
      setNewPlanDetected(true);
    }
  }, [plan, waitingForUpdatedPlan]);

  // 状態監視とリダイレクト処理
  useEffect(() => {
    if (!research) return;
    
    // フィードバック提出後の処理フロー
    if (waitingForUpdatedPlan) {
      // 新しいプランが検出された、かつフィードバック待ち状態の場合
      if (newPlanDetected) {
        console.log("更新されたプランが検出されました。フィードバック画面を更新します。");
        setWaitingForUpdatedPlan(false);
        originalPlanRef.current = null;
        setNewPlanDetected(false);
      }
      // 特定の状態になったらリダイレクト
      else if (['completed', 'error'].includes(research.status)) {
        console.log("リサーチが完了かエラー状態になりました。ステータス画面に戻ります。");
        router.push(`/research/${researchId}`);
      }
      // 処理中は継続して待機
      else if (research.status === 'processing_feedback') {
        console.log("フィードバックを処理中です。待機を継続します。");
        // 処理中は引き続き待機
      }
    } 
    // 初期表示時のチェック（フィードバック待ち状態以外ならリダイレクト）
    else if (!waitingForUpdatedPlan && research.status !== 'waiting_for_feedback') {
      router.push(`/research/${researchId}`);
    }
  }, [research, researchId, router, waitingForUpdatedPlan, newPlanDetected]);

  // 定期的なポーリング設定
  useEffect(() => {
    if (!waitingForUpdatedPlan) return;
    
    // 最初のポーリングをすぐに実行
    console.log("初回ポーリングを実行...");
    refetchStatus();
    refetchPlan();
    
    const intervalId = setInterval(() => {
      console.log("ステータスとプランをポーリング中...");
      refetchStatus();
      refetchPlan();
    }, 3000); // 3秒間隔に短縮
    
    return () => clearInterval(intervalId);
  }, [waitingForUpdatedPlan, refetchStatus, refetchPlan]);

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

  // 更新されたプランを待機中の表示
  if (waitingForUpdatedPlan) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-4xl">
        <div className="flex items-center gap-2 text-gray-600 mb-6 hover:text-gray-800 transition-colors">
          <Link href={`/research/${researchId}`} className="flex items-center gap-2">
            <ArrowLeft size={16} />
            <span>リサーチ詳細に戻る</span>
          </Link>
        </div>
        
        <div className="text-center py-16">
          <Loader2 className="h-16 w-16 animate-spin mx-auto mb-6 text-blue-600" />
          <h2 className="text-2xl font-bold mb-4">フィードバックを処理中...</h2>
          <p className="text-gray-600 mb-6">
            リサーチプランを更新しています。このプロセスには数分かかる場合があります。
            <br />更新が完了すると自動的に新しいプランが表示されます。
          </p>
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
          <FeedbackForm 
            researchId={researchId} 
            sections={sections} 
            onFeedbackSubmitted={handleFeedbackSubmitted} 
          />
        </CardContent>
      </Card>
    </div>
  );
}