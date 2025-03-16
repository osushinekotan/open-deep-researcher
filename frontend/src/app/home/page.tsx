import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LayoutDashboard, BookOpen, Rocket, ArrowRight, LogIn } from "lucide-react";

export default function HomePage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">Open Deep Researcher</h1>
        <p className="text-xl text-gray-500 max-w-3xl mx-auto">
          AIを活用した高度なリサーチツール
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
        <Card className="shadow-md hover:shadow-lg transition-shadow">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <LayoutDashboard className="h-5 w-5 text-blue-500" />
              <span>ダッシュボード</span>
            </CardTitle>
            <CardDescription>
              進行中のリサーチを確認
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-gray-600">
              すべてのリサーチプロジェクトを一覧表示し、進捗状況を管理します。
            </p>
            <Link href="/dashboard">
              <Button className="w-full flex items-center justify-center gap-1">
                <span>ダッシュボードを開く</span>
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="shadow-md hover:shadow-lg transition-shadow">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-green-500" />
              <span>使い方</span>
            </CardTitle>
            <CardDescription>
              リサーチツールの活用法
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-gray-600">
              Open Deep Researcherの機能や設定項目の詳細な説明をご覧いただけます。
            </p>
            <Link href="/guide">
              <Button className="w-full flex items-center justify-center gap-1 bg-green-600 hover:bg-green-700">
                <span>ガイドを見る</span>
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="shadow-md hover:shadow-lg transition-shadow">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Rocket className="h-5 w-5 text-purple-500" />
              <span>新しいリサーチ</span>
            </CardTitle>
            <CardDescription>
              リサーチプロジェクトを開始
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-gray-600">
              新しいトピックのリサーチを作成し、AIによる深い調査を開始しましょう。
            </p>
            <Link href="/new-research">
              <Button className="w-full flex items-center justify-center gap-1 bg-purple-600 hover:bg-purple-700">
                <span>新規リサーチを作成</span>
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      <div className="mt-12 text-center">
        <h2 className="text-2xl font-bold mb-4">より深く、より速いリサーチ</h2>
        <p className="text-gray-600 max-w-3xl mx-auto mb-6">
          Open Deep Researcherは、複数のAIモデルと検索エンジンを組み合わせ、学術論文から特許情報まで幅広い情報源から高品質なリサーチレポートを生成します。
        </p>
        <Link href="/new-research">
          <Button size="lg" className="bg-blue-600 hover:bg-blue-700">
            Start your research
          </Button>
        </Link>
      </div>
    </div>
  );
}