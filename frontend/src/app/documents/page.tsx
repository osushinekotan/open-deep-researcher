"use client";

import { useState } from "react";
import { FileUpload } from "@/components/documents/file-upload";
import { FileList } from "@/components/documents/file-list";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useAuthStore } from "@/store/auth-store";
import { ProtectedRoute } from "@/components/protected-route";
import { FileArchive } from "lucide-react";

export default function DocumentsPage() {
  const { username } = useAuthStore();
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [enabledFiles, setEnabledFiles] = useState<string[]>([]);

  const handleUploadSuccess = () => {
    // ファイルリストを更新
    setRefreshTrigger(prev => prev + 1);
  };

  const handleSelectionChange = (files: string[]) => {
    setEnabledFiles(files);
  };

  return (
    <ProtectedRoute>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <FileArchive className="h-7 w-7 text-blue-500" />
            <span>ドキュメント管理</span>
          </h1>
          <p className="text-gray-500 mt-2">
            {username ? `${username} さんのドキュメントを管理します` : 'ドキュメントを管理します'}
          </p>
        </div>

        <div className="grid grid-cols-1 gap-8">
          <Card>
            <CardHeader>
              <CardTitle>ファイルアップロード</CardTitle>
              <CardDescription>
                リサーチで使用するファイルをアップロードします
              </CardDescription>
            </CardHeader>
            <CardContent>
              <FileUpload 
                onUploadSuccess={handleUploadSuccess}
                maxFiles={5}
              />
            </CardContent>
          </Card>

          <Separator />

          <Card>
            <CardHeader>
              <CardTitle>ファイル一覧</CardTitle>
              <CardDescription>
                アップロードしたファイルの管理と選択を行います
              </CardDescription>
            </CardHeader>
            <CardContent>
              <FileList 
                onSelectionChange={handleSelectionChange} 
                refreshTrigger={refreshTrigger}
              />
              
              {enabledFiles.length > 0 && (
                <div className="mt-4 p-4 bg-blue-50 rounded-md text-sm">
                  <p className="font-medium text-blue-700 mb-1">選択中のファイル ({enabledFiles.length}件)</p>
                  <ul className="list-disc pl-5 text-blue-600 space-y-1">
                    {enabledFiles.map(file => (
                      <li key={file}>{file}</li>
                    ))}
                  </ul>
                  <p className="mt-2 text-gray-600">
                    これらのファイルはローカル検索オプションを有効にした場合にリサーチで使用されます。
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </ProtectedRoute>
  );
}