"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useResearchStatus, useResearchResult } from "@/hooks/use-research";
import { ReportViewer } from "@/components/research/report-viewer";
import { Loader2 } from "lucide-react";

// クライアントコンポーネント - パラメータはプロパティとして受け取る
export function ResultClient({ researchId }: { researchId: string }) {
  const router = useRouter();
  
  const { 
    data: research, 
    isLoading: statusLoading, 
    error: statusError 
  } = useResearchStatus(researchId);
  
  const { 
    data: result, 
    isLoading: resultLoading, 
    error: resultError 
  } = useResearchResult(researchId);

  const isLoading = statusLoading || resultLoading;
  const error = statusError || resultError;

  // エラー時のハンドリング
  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-4xl">
        <div className="text-center py-16 bg-red-50 rounded-lg border border-red-100">
          <h2 className="text-2xl font-bold text-red-600 mb-4">エラーが発生しました</h2>
          <p className="text-gray-600 mb-6">リサーチ結果の読み込み中にエラーが発生しました。</p>
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

  // ローディング時の表示
  if (isLoading || !research || !result) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <Loader2 className="h-12 w-12 animate-spin mx-auto mb-6 text-blue-600" />
        <h3 className="text-xl font-semibold mb-2">リサーチ結果を読み込み中...</h3>
        <p className="text-gray-500">しばらくお待ちください</p>
      </div>
    );
  }

  // 完了状態でない場合はリサーチ詳細ページにリダイレクト
  if (research.status !== 'completed') {
    router.push(`/research/${researchId}`);
    return null;
  }

  // 最終レポートがない場合
  if (!result.final_report) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-4xl">
        <div className="text-center py-16 bg-yellow-50 rounded-lg border border-yellow-100">
          <h2 className="text-2xl font-bold text-yellow-600 mb-4">レポートが見つかりません</h2>
          <p className="text-gray-600 mb-6">リサーチは完了していますが、最終レポートが見つかりませんでした。</p>
          <Button variant="outline" onClick={() => router.push('/dashboard')}>
            ダッシュボードに戻る
          </Button>
        </div>
      </div>
    );
  }

  // レポートのパース
  let reportSections = [];
  let references = [];
  
  try {
    // 簡易的なパース処理（実際の出力形式に合わせて調整が必要）
    const reportText = result.final_report;
    
    // セクションの取得（例としての実装）
    const sections = reportText.split(/(?=##\s)/);
    
    reportSections = sections.map((section, index) => {
      const titleMatch = section.match(/^##\s+(.+)$/m);
      const title = titleMatch ? titleMatch[1] : `セクション ${index + 1}`;
      const content = section.replace(/^##\s+.+$/m, '').trim();
      
      return {
        id: `section-${index}`,
        title,
        content
      };
    });
    
    // 参考文献があれば抽出（例としての実装）
    const referenceSection = reportText.match(/## 参考文献\s+([\s\S]+)$/);
    if (referenceSection) {
      const refLines = referenceSection[1].split(/\n+/).filter(Boolean);
      references = refLines.map((line, index) => {
        return {
          id: `ref-${index}`,
          title: line,
          authors: '',
          year: '',
          url: '#'
        };
      });
    }
  } catch (e) {
    console.error('レポートパースエラー:', e);
    // パースに失敗した場合はシンプルな表示
    reportSections = [{
      id: 'section-0',
      title: 'レポート',
      content: result.final_report
    }];
  }

  // 作成日・完了日
  const createdAt = research.created_at || new Date().toISOString();
  const completedAt = result.completed_at || new Date().toISOString();

  return (
    <ReportViewer
      topic={research.topic}
      createdAt={createdAt}
      completedAt={completedAt}
      sections={reportSections}
      references={references}
    />
  );
}