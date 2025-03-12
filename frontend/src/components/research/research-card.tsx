"use client";

import Link from "next/link";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Clock, FileText, RefreshCw, ThumbsUp } from "lucide-react";
import { StatusBadge } from "./status-badge";
import { formatDate, getStatusInfo } from "@/lib/utils";
import { ResearchStatus } from "@/types/api";

interface ResearchCardProps {
  research: ResearchStatus;
}

export function ResearchCard({ research }: ResearchCardProps) {
  const { status, topic, research_id: id, progress = 0 } = research;
  const statusInfo = getStatusInfo(status);
  
  // 進捗率を整数に変換（APIから小数で返される場合は100倍する）
  const progressPercentage = typeof progress === 'number' && progress <= 1 
    ? Math.round(progress * 100) 
    : Math.round(progress);
  
  // 日付表示用（完了した場合はcompleted_atを使用、それ以外は現在日時）
  const displayDate = status === 'completed' && research.completed_at 
    ? research.completed_at 
    : new Date().toISOString();
  
  return (
    <Card className="overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-300 border border-gray-200">
      <CardHeader className="pb-2 space-y-2">
        <div className="flex justify-between items-start">
          <StatusBadge status={status} />
          <div className="text-sm text-gray-500 flex items-center">
            <Clock size={14} className="mr-1" />
            {formatDate(displayDate)}
          </div>
        </div>
        <CardTitle className="text-lg font-semibold mt-1 line-clamp-2">{topic}</CardTitle>
      </CardHeader>
      <CardContent className="pb-4">
        <div className="mt-2">
          <div className="flex justify-between text-sm mb-1.5">
            <span className="text-gray-600">進捗状況</span>
            <span className={statusInfo.textColor}>{progressPercentage}%</span>
          </div>
          <Progress value={progressPercentage} className="h-2 bg-gray-100" />
        </div>
      </CardContent>
      <CardFooter className="border-t pt-3 pb-3 bg-gray-50">
        {status === 'waiting_for_feedback' ? (
          <Link href={`/research/${id}/feedback`} className="w-full">
            <Button 
              variant="outline" 
              className="w-full flex items-center justify-center gap-1.5 border-yellow-500 text-yellow-600 hover:bg-yellow-50"
            >
              <ThumbsUp size={16} />
              <span>フィードバック</span>
            </Button>
          </Link>
        ) : status === 'completed' ? (
          <Link href={`/research/${id}/result`} className="w-full">
            <Button 
              variant="outline" 
              className="w-full flex items-center justify-center gap-1.5 border-green-500 text-green-600 hover:bg-green-50"
            >
              <FileText size={16} />
              <span>結果を見る</span>
            </Button>
          </Link>
        ) : (
          <Link href={`/research/${id}`} className="w-full">
            <Button 
              variant="outline" 
              className="w-full flex items-center justify-center gap-1.5 border-blue-500 text-blue-600 hover:bg-blue-50"
            >
              <RefreshCw size={16} />
              <span>ステータス確認</span>
            </Button>
          </Link>
        )}
      </CardFooter>
    </Card>
  );
}