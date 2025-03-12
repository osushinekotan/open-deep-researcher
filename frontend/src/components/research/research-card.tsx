"use client";

import { useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Clock, FileText, RefreshCw, ThumbsUp, Trash, AlertCircle } from "lucide-react";
import { StatusBadge } from "./status-badge";
import { formatDate, getStatusInfo } from "@/lib/utils";
import { ResearchStatus } from "@/types/api";
import { useDeleteResearch } from "@/hooks/use-research";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface ResearchCardProps {
  research: ResearchStatus;
}

export function ResearchCard({ research }: ResearchCardProps) {
  const { status, topic, research_id: id, progress = 0 } = research;
  const statusInfo = getStatusInfo(status);

  // 進捗率の計算（小数の場合は100倍する）
  const progressPercentage =
    typeof progress === "number" && progress <= 1
      ? Math.round(progress * 100)
      : Math.round(progress);

  // 日付表示：完了ならcompleted_at、その他は現在日時
  const displayDate =
    status === "completed" && research.completed_at
      ? research.completed_at
      : new Date().toISOString();

  // 削除処理用のフックとダイアログの開閉管理
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const { mutate: deleteResearch, isPending: isDeleting } = useDeleteResearch();

  const handleDeleteConfirm = () => {
    deleteResearch(id);
    setIsDeleteDialogOpen(false);
  };

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
      <CardFooter className="border-t pt-3 pb-3 bg-gray-50 flex gap-2">
        <div className="flex-1">
          {status === "waiting_for_feedback" ? (
            <Link href={`/research/${id}/feedback`} className="w-full">
              <Button
                variant="outline"
                className="w-full flex items-center justify-center gap-1.5 border-yellow-500 text-yellow-600 hover:bg-yellow-50"
              >
                <ThumbsUp size={16} />
                <span>フィードバック</span>
              </Button>
            </Link>
          ) : status === "completed" ? (
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
        </div>
        {/* 削除ボタン */}
        <Button
          variant="outline"
          size="icon"
          className="flex-shrink-0 border-red-300 text-red-600 hover:bg-red-50"
          onClick={() => setIsDeleteDialogOpen(true)}
          disabled={isDeleting}
          title="削除"
        >
          <Trash size={16} />
        </Button>
        {/* 削除確認ダイアログ */}
        <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle className="flex items-center gap-2">
                <AlertCircle className="text-red-500" size={20} />
                リサーチの削除
              </AlertDialogTitle>
              <AlertDialogDescription>
                このリサーチを削除しますか？この操作は元に戻すことができません。
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={isDeleting}>キャンセル</AlertDialogCancel>
              <AlertDialogAction
                className="bg-red-600 hover:bg-red-700"
                onClick={handleDeleteConfirm}
                disabled={isDeleting}
              >
                {isDeleting ? "削除中..." : "削除する"}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </CardFooter>
    </Card>
  );
}
