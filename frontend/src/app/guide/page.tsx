import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  BookOpen,
  Settings,
  Search,
  FileText,
  Cpu,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Rocket,
} from "lucide-react";

export default function GuidePage() {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-12">
        <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
          <BookOpen className="h-6 w-6 text-blue-500" />
          Open Deep Researcher 使い方
        </h1>
        <p className="text-gray-500 text-lg">
          AIを活用したリサーチツールの活用方法をご紹介します
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8 mb-12">
        <Card>
          <CardHeader>
            <CardTitle className="text-xl">はじめに</CardTitle>
            <CardDescription>Open Deep Researcherとは</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p>
              Open Deep Researcherは、AIを活用して複雑なトピックに関する深い調査を効率的に行うためのツールです。
              複数のAIモデルと検索エンジンを組み合わせることで、学術論文から特許情報まで幅広い情報源から高品質なリサーチレポートを生成します。
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
              <div className="flex flex-col items-center text-center p-4 bg-blue-50 rounded-lg">
                <CheckCircle2 className="h-10 w-10 text-blue-500 mb-2" />
                <h3 className="font-medium mb-1">効率的な調査</h3>
                <p className="text-sm text-gray-600">
                  AIが多様な情報源から関連情報を収集し分析
                </p>
              </div>
              <div className="flex flex-col items-center text-center p-4 bg-green-50 rounded-lg">
                <CheckCircle2 className="h-10 w-10 text-green-500 mb-2" />
                <h3 className="font-medium mb-1">深い洞察</h3>
                <p className="text-sm text-gray-600">
                  複雑なトピックを多角的に分析し理解を深める
                </p>
              </div>
              <div className="flex flex-col items-center text-center p-4 bg-purple-50 rounded-lg">
                <CheckCircle2 className="h-10 w-10 text-purple-500 mb-2" />
                <h3 className="font-medium mb-1">カスタマイズ</h3>
                <p className="text-sm text-gray-600">
                  様々なパラメータを調整して理想的な結果を得る
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2">
              <Rocket className="h-5 w-5" />
              基本的な使い方
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="item-1">
                <AccordionTrigger>1. リサーチの作成</AccordionTrigger>
                <AccordionContent className="space-y-3 p-4 bg-gray-50 rounded-md">
                  <p>
                    ダッシュボードから「New Research」ボタンをクリックするか、ナビゲーションメニューから「新しいリサーチ」を選択します。
                  </p>
                  <p>
                    リサーチしたいトピックや質問を入力します。質問形式で入力すると、その回答を探すリサーチが行われます。
                  </p>
                  <div className="flex items-center p-2 bg-blue-50 rounded border border-blue-100 text-sm">
                    <AlertCircle className="h-4 w-4 text-blue-500 mr-2 flex-shrink-0" />
                    <span>
                      より具体的なトピックや質問を入力するほど、関連性の高い結果が得られます。
                    </span>
                  </div>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="item-2">
                <AccordionTrigger>2. リサーチ設定のカスタマイズ</AccordionTrigger>
                <AccordionContent className="space-y-3 p-4 bg-gray-50 rounded-md">
                  <p>
                    リサーチフォームでは、以下の設定をカスタマイズできます：
                  </p>
                  <ul className="list-disc pl-5 space-y-1">
                    <li>
                      <strong>基本設定</strong>: 言語やディープリサーチの有効化など
                    </li>
                    <li>
                      <strong>レポート設定</strong>: 単語数制限やレポート構造
                    </li>
                    <li>
                      <strong>モデル設定</strong>: 使用するAIモデルの選択
                    </li>
                    <li>
                      <strong>検索設定</strong>: 検索プロバイダーやクエリ数
                    </li>
                  </ul>
                  <p>
                    デフォルト設定でも高品質な結果が得られますが、特定のニーズに応じてカスタマイズすることで、より適切な結果を得ることができます。
                  </p>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="item-3">
                <AccordionTrigger>3. リサーチプランの確認とフィードバック</AccordionTrigger>
                <AccordionContent className="space-y-3 p-4 bg-gray-50 rounded-md">
                  <p>
                    「フィードバックをスキップ」オプションをオフにしている場合、AIがリサーチプランを生成した後、そのプランを確認するためのページが表示されます。
                  </p>
                  <p>
                    提案されたセクション構成を確認し、必要に応じてフィードバックを提供できます。例えば：
                  </p>
                  <ul className="list-disc pl-5 space-y-1">
                    <li>新しいセクションの追加を提案</li>
                    <li>既存のセクションの変更や削除を提案</li>
                    <li>特定の側面に焦点を当てるよう指示</li>
                    <li>使用する検索プロバイダーの変更s指示</li>
                  </ul>
                  <p>
                    フィードバックなしでプランを承認することもできます。その場合は「プランを承認」ボタンをクリックします。
                  </p>
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="item-4">
                <AccordionTrigger>4. リサーチの進行と結果の確認</AccordionTrigger>
                <AccordionContent className="space-y-3 p-4 bg-gray-50 rounded-md">
                  <p>
                    リサーチが開始されると、ダッシュボードからその進捗状況を確認できます。各セクションが順番に研究され、レポートが作成されます。
                  </p>
                  <p>
                    リサーチが完了すると、ダッシュボードの対応するカードに「結果を見る」ボタンが表示されます。
                  </p>
                  <p>
                    結果ページでは、生成されたレポートを閲覧できます。
                  </p>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2">
              <Settings className="h-5 w-5" />
              詳細設定ガイド
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-medium mb-2 flex items-center gap-2">
                  <Search className="h-4 w-4" />
                  検索設定
                </h3>
                <p className="text-sm text-gray-600 mb-2">
                  リサーチに使用する検索プロバイダーやクエリ数などを設定できます。
                </p>
                <ul className="text-sm list-disc pl-5 space-y-1 text-gray-600">
                  <li>Tavily: 汎用ウェブ検索</li>
                  <li>arXiv: 学術論文検索</li>
                </ul>
              </div>

              <div>
                <h3 className="font-medium mb-2 flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  レポート設定
                </h3>
                <p className="text-sm text-gray-600 mb-2">
                  生成されるレポートの構造や単語数制限を設定できます。
                </p>
                <ul className="text-sm list-disc pl-5 space-y-1 text-gray-600">
                  <li>レポート構造: 自動またはカスタム</li>
                  <li>セクション単語数: 500-2000単語</li>
                  <li>序論・結論単語数: 200-1000単語</li>
                </ul>
              </div>

              <div>
                <h3 className="font-medium mb-2 flex items-center gap-2">
                  <Cpu className="h-4 w-4" />
                  モデル設定
                </h3>
                <p className="text-sm text-gray-600 mb-2">
                  リサーチに使用するAIモデルを選択できます。
                </p>
                <ul className="text-sm list-disc pl-5 space-y-1 text-gray-600">
                  <li>プランナーモデル: リサーチプラン作成</li>
                  <li>ライターモデル: セクション執筆</li>
                  <li>結論ライターモデル: 結論の執筆</li>
                </ul>
              </div>

              <div>
                <h3 className="font-medium mb-2 flex items-center gap-2">
                  <HelpCircle className="h-4 w-4" />
                  その他の設定
                </h3>
                <p className="text-sm text-gray-600 mb-2">
                  深掘り調査やフィードバックに関するオプション。
                </p>
                <ul className="text-sm list-disc pl-5 space-y-1 text-gray-600">
                  <li>Deep Research: 探索的リサーチの有効化</li>
                  <li>探索の深さと幅: 調査の詳細度</li>
                  <li>フィードバックスキップ: 自動実行</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="flex justify-center mt-12">
        <Link href="/new-research">
          <Button className="bg-blue-600 hover:bg-blue-700 flex items-center gap-2" size="lg">
            <span>リサーチを始める</span>
            <ArrowRight className="h-5 w-5" />
          </Button>
        </Link>
      </div>
    </div>
  );
}