"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ResearchCard } from "@/components/research/research-card";
import { Search, Rocket } from "lucide-react";
import { useResearchList } from "@/hooks/use-research";
import { ResearchStatus } from "@/types/api";
import { Input } from "@/components/ui/input";

export default function DashboardPage() {
  const { data: researches, isLoading, error, refetch } = useResearchList();
  const [searchQuery, setSearchQuery] = useState("");
  
  // スケルトンローディング用のダミーデータ
  const skeletonItems = Array(3).fill(null);

  // 検索フィルター
  const filteredResearches = researches?.filter(research => 
    research.topic.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">リサーチダッシュボード</h1>
        <p className="text-gray-500 mt-2">あなたのリサーチプロジェクトを管理します</p>
      </div>

      {researches && researches.length > 0 && (
        <div className="mb-6 relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search size={18} className="text-gray-400" />
          </div>
          <Input
            type="text"
            placeholder="リサーチを検索..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      )}

      {isLoading ? (
        // ローディング中
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {skeletonItems.map((_, index) => (
            <div 
              key={index} 
              className="h-52 bg-gray-100 rounded-lg animate-pulse"
            />
          ))}
        </div>
      ) : error ? (
        // エラー発生時
        <div className="p-8 text-center bg-red-50 rounded-lg border border-red-100">
          <p className="text-red-500 mb-4">データの読み込み中にエラーが発生しました</p>
          <Button 
            variant="outline" 
            onClick={() => refetch()}
            className="border-red-300 text-red-600 hover:bg-red-50"
          >
            再読み込み
          </Button>
        </div>
      ) : !researches || researches.length === 0 ? (
        // データが空の場合
        <div className="text-center py-16 bg-white-50 rounded-lg border border-gray-200">
          <Link href="/new-research">
            <p className="flex items-center justify-center gap-1.5 text-blue-600 text-xl mb-6">
              新しいリサーチを作成して始めましょう
              <Rocket size={20} />
            </p>
          </Link>
        </div>
      ) : filteredResearches?.length === 0 ? (
        // 検索結果なし
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-gray-600 mb-4">「{searchQuery}」に一致するリサーチが見つかりませんでした</p>
          <Button 
            variant="outline" 
            onClick={() => setSearchQuery("")}
            className="border-gray-300"
          >
            検索をクリア
          </Button>
        </div>
      ) : (
        // リサーチデータの表示
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredResearches?.map((research: ResearchStatus) => (
            <ResearchCard key={research.research_id} research={research} />
          ))}
        </div>
      )}
    </div>
  );
}