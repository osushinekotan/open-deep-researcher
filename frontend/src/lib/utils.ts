import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

// クラス名を結合するユーティリティ
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// 日付をフォーマットするユーティリティ
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('ja-JP', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
}

// リサーチステータスのラベルとカラーを取得
export function getStatusInfo(status: string): { label: string; color: string; textColor: string } {
  switch (status) {
    case 'completed':
      return { label: '完了', color: 'bg-green-500', textColor: 'text-green-500' };
    case 'waiting_for_feedback':
      return { label: 'フィードバック待ち', color: 'bg-yellow-500', textColor: 'text-yellow-500' };
    case 'researching_sections':
    case 'processing_sections':
      return { label: 'リサーチ中', color: 'bg-blue-500', textColor: 'text-blue-500' };
    case 'planning':
      return { label: 'プラン作成中', color: 'bg-purple-500', textColor: 'text-purple-500' };
    case 'initializing':
      return { label: '初期化中', color: 'bg-gray-500', textColor: 'text-gray-500' };
    case 'error':
      return { label: 'エラー', color: 'bg-red-500', textColor: 'text-red-500' };
    default:
      return { label: '進行中', color: 'bg-gray-500', textColor: 'text-gray-500' };
  }
}

// リサーチプランのサンプルデータ (開発用)
export const sampleResearchPlan = {
  sections: [
    {
      name: "AIの現状と基礎技術",
      description: "現在のAI技術の概要、主要なアプローチ、および基盤となる技術について解説。"
    },
    {
      name: "大規模言語モデルの発展",
      description: "GPT、LLaMA、Claudeなどの大規模言語モデルの進化と特徴を分析。"
    },
    {
      name: "AIの産業応用と事例",
      description: "様々な産業でのAI活用事例と、それによるビジネス変革について調査。"
    },
    {
      name: "AIの倫理的・社会的課題",
      description: "AIの普及に伴う倫理的問題、バイアス、プライバシー問題などの課題を検討。"
    },
    {
      name: "将来展望と研究動向",
      description: "AIの今後の発展方向性と最先端の研究動向について予測。"
    }
  ]
};