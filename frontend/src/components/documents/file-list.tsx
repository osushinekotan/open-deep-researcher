"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Trash2, RefreshCw, FileText, Loader2 } from "lucide-react";
import { documentService } from "@/services/document-service";
import { DocumentStatus } from "@/types/api";
import { useAuthStore } from "@/store/auth-store"; // ユーザー認証情報を取得

interface FileListProps {
  onSelectionChange?: (enabledFiles: string[]) => void;
  refreshTrigger?: number;
}

export function FileList({ onSelectionChange, refreshTrigger = 0 }: FileListProps) {
  const [documents, setDocuments] = useState<DocumentStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  const { username } = useAuthStore(); // 現在のユーザー名を取得

  // ファイル一覧を取得
  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      // ユーザー名を渡してファイル一覧を取得
      const data = await documentService.listDocuments(username || undefined);
      setDocuments(data);
      // 有効なファイル一覧を親コンポーネントに通知
      if (onSelectionChange) {
        const enabledFiles = data
          .filter(doc => doc.is_enabled)
          .map(doc => doc.filename);
        onSelectionChange(enabledFiles);
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: "ファイル一覧の取得に失敗しました。"
      });
    } finally {
      setIsLoading(false);
    }
  };

  // 初回レンダリング時とrefreshTriggerが変更されたときにファイル一覧を取得
  useEffect(() => {
    fetchDocuments();
  }, [refreshTrigger, username]); // usernameも依存リストに追加

  // ファイルの有効/無効を切り替え
  const toggleFileEnabled = async (filename: string, enabled: boolean) => {
    try {
      // ユーザー名を渡して状態を更新
      await documentService.toggleDocumentEnabled(filename, enabled, username || undefined);
      
      // ステートを更新
      setDocuments(prev => 
        prev.map(doc => 
          doc.filename === filename 
            ? { ...doc, is_enabled: enabled } 
            : doc
        )
      );
      
      // 有効なファイル一覧を親コンポーネントに通知
      if (onSelectionChange) {
        const enabledFiles = documents
          .map(doc => 
            doc.filename === filename 
              ? { ...doc, is_enabled: enabled } 
              : doc
          )
          .filter(doc => doc.is_enabled)
          .map(doc => doc.filename);
        onSelectionChange(enabledFiles);
      }

      setMessage({
        type: 'success',
        text: `${filename} を${enabled ? '有効' : '無効'}にしました。`
      });
      
      // 数秒後にメッセージを消す
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      setMessage({
        type: 'error',
        text: `${filename} の状態更新に失敗しました。`
      });
    }
  };

  // ファイルを削除
  const deleteFile = async (filename: string) => {
    if (window.confirm(`「${filename}」を削除します。よろしいですか？`)) {
      setIsDeleting(filename);
      try {
        // ユーザー名を渡してファイルを削除
        await documentService.deleteDocument(filename, username || undefined);
        
        // ドキュメント一覧から削除したファイルを除外
        setDocuments(prev => prev.filter(doc => doc.filename !== filename));
        
        // 有効なファイル一覧を親コンポーネントに通知
        if (onSelectionChange) {
          const enabledFiles = documents
            .filter(doc => doc.is_enabled && doc.filename !== filename)
            .map(doc => doc.filename);
          onSelectionChange(enabledFiles);
        }

        setMessage({
          type: 'success',
          text: `${filename} を削除しました。`
        });
        
        // 数秒後にメッセージを消す
        setTimeout(() => setMessage(null), 3000);
      } catch (error) {
        setMessage({
          type: 'error',
          text: `${filename} の削除に失敗しました。`
        });
      } finally {
        setIsDeleting(null);
      }
    }
  };

  // ファイルサイズを見やすく表示
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    else if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    else return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
  };

  // 日付をフォーマット
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('ja-JP', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-base font-medium">アップロード済みファイル</h3>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchDocuments}
          disabled={isLoading}
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
        </Button>
      </div>
      
      {message && (
        <div className={`p-3 rounded-md ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
          {message.text}
        </div>
      )}
      
      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      ) : documents.length === 0 ? (
        <div className="text-center py-8 bg-gray-50 rounded-md border">
          <FileText className="mx-auto h-10 w-10 text-gray-400 mb-2" />
          <p className="text-gray-500">アップロードされたファイルはありません</p>
        </div>
      ) : (
        <div className="border rounded-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ファイル名
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    サイズ
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    アップロード日
                  </th>
                  <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    使用
                  </th>
                  <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {documents.map((doc) => (
                  <tr key={doc.filename}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900 truncate max-w-xs">
                        {doc.filename}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">{formatFileSize(doc.size)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">{formatDate(doc.uploaded_at)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <Switch 
                        checked={doc.is_enabled}
                        onCheckedChange={(checked) => toggleFileEnabled(doc.filename, checked)}
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => deleteFile(doc.filename)}
                        disabled={isDeleting === doc.filename}
                        className="text-red-500 hover:text-red-700 hover:bg-red-50"
                      >
                        {isDeleting === doc.filename ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}