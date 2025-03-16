"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Upload, Loader2 } from "lucide-react";
import { documentService } from "@/services/document-service";
import { useAuthStore } from "@/store/auth-store"; // ユーザー認証情報を取得

interface FileUploadProps {
  onUploadSuccess?: () => void;
  maxFiles?: number;
}

export function FileUpload({ onUploadSuccess, maxFiles = 5 }: FileUploadProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  const { username } = useAuthStore(); // 現在のユーザー名を取得

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const fileList = Array.from(e.target.files);
      
      // 選択されたファイル数をチェック
      if (fileList.length > maxFiles) {
        setMessage({
          type: 'error',
          text: `一度に${maxFiles}ファイルまでしかアップロードできません。`
        });
        return;
      }
      
      setFiles(fileList);
      setMessage(null);
    }
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setMessage({
        type: 'error',
        text: "アップロードするファイルを選択してください。"
      });
      return;
    }
    
    setIsUploading(true);
    
    try {
      // ユーザー名を渡してファイルをアップロード
      const result = await documentService.uploadDocuments(files, username || undefined);
      
      setMessage({
        type: 'success',
        text: `${result.filenames.length}個のファイルをアップロードしました。`
      });
      
      // 入力フィールドをリセット
      setFiles([]);
      if (onUploadSuccess) {
        onUploadSuccess();
      }
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || "ファイルのアップロード中にエラーが発生しました。"
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-2">
        <Input
          type="file"
          multiple
          onChange={handleFileChange}
          disabled={isUploading}
          className="cursor-pointer"
          accept=".txt,.pdf,.docx,.csv,.xlsx,.md,.html"
        />
        
        {files.length > 0 && (
          <div className="text-sm text-gray-500">
            {files.length}個のファイルが選択されています
          </div>
        )}
      </div>
      
      <Button
        onClick={handleUpload}
        disabled={isUploading || files.length === 0}
        className="w-full"
      >
        {isUploading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            アップロード中...
          </>
        ) : (
          <>
            <Upload className="mr-2 h-4 w-4" />
            ファイルをアップロード
          </>
        )}
      </Button>

      {message && (
        <div className={`p-3 rounded-md ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
          {message.text}
        </div>
      )}
    </div>
  );
}