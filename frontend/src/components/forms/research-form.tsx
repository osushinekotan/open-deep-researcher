"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Card, 
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
  CardFooter
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Info, Rocket, Settings, Search, Layers } from 'lucide-react';
import { useResearchStore } from '@/store/research-store';
import { useStartResearch } from '@/hooks/use-research';
import { 
  PlannerProviderEnum, 
  WriterProviderEnum, 
  SearchProviderEnum 
} from '@/types/api';

export function ResearchForm() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState('basic');
  
  // グローバルストアからフォーム状態を取得
  const { topic, config, setTopic, updateConfig, resetForm } = useResearchStore();
  
  // リサーチ開始ミューテーション
  const { mutate: startResearch, isPending } = useStartResearch();
  
  // フォーム送信ハンドラ
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!topic.trim()) {
      alert('トピックを入力してください');
      return;
    }
    
    startResearch({ topic, config }, {
      onSuccess: (data) => {
        // 成功したらリセットして詳細ページに移動
        resetForm();
        router.push(`/research/${data.research_id}`);
      },
      onError: (error) => {
        console.error('リサーチ開始エラー:', error);
        alert('リサーチの開始に失敗しました。もう一度お試しください。');
      }
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="text-xl flex items-center gap-2">
            <Rocket size={20} />
            リサーチトピック
          </CardTitle>
          <CardDescription>
            探求したいトピックや質問を入力してください
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <Label htmlFor="topic" className="text-base font-medium">
                トピック
              </Label>
              <Textarea
                id="topic"
                placeholder="例: AIの発展が今後10年間で労働市場に与える影響について調査してください"
                className="h-32 mt-2"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                disabled={isPending}
                required
              />
              <p className="text-sm text-gray-500 mt-1">
                質問形式で入力すると、より的確な回答が得られます
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="basic" className="mb-8" value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-2 mb-4">
          <TabsTrigger value="basic" className="flex items-center gap-2">
            <Info size={16} />
            <span>基本設定</span>
          </TabsTrigger>
          <TabsTrigger value="advanced" className="flex items-center gap-2">
            <Settings size={16} />
            <span>詳細設定</span>
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="basic">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">基本設定</CardTitle>
              <CardDescription>
                リサーチの基本的な動作を設定します
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="skip_feedback" className="flex flex-col">
                    <div className="font-medium">フィードバックをスキップ</div>
                    <p className="text-sm text-gray-500">プランの確認をスキップして自動的に実行</p>
                  </Label>
                  <Switch 
                    id="skip_feedback" 
                    checked={config.skip_human_feedback}
                    onCheckedChange={(checked) => updateConfig({ skip_human_feedback: checked })}
                    disabled={isPending}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="language">言語設定</Label>
                <Select 
                  defaultValue={config.language} 
                  onValueChange={(value) => updateConfig({ language: value })}
                  disabled={isPending}
                >
                  <SelectTrigger id="language">
                    <SelectValue placeholder="言語を選択" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="japanese">日本語</SelectItem>
                    <SelectItem value="english">英語</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="deep_research" className="flex flex-col">
                    <div className="font-medium">詳細なリサーチを有効化</div>
                    <p className="text-sm text-gray-500">より詳細で深い分析を行います</p>
                  </Label>
                  <Switch 
                    id="deep_research" 
                    defaultChecked={config.enable_deep_research}
                    onCheckedChange={(checked) => updateConfig({ enable_deep_research: checked })}
                    disabled={isPending}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="advanced">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">詳細設定</CardTitle>
              <CardDescription>
                リサーチの詳細なパラメータを調整します
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* モデル設定セクション */}
              <Card className="border-gray-200">
                <CardHeader className="pb-3 pt-4">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Settings size={16} />
                    モデル設定
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 pt-0">
                  <div className="space-y-2">
                    <Label htmlFor="planner_provider">プランナープロバイダー</Label>
                    <Select 
                      defaultValue={config.planner_provider} 
                      onValueChange={(value) => updateConfig({ 
                        planner_provider: value as PlannerProviderEnum 
                      })}
                      disabled={isPending}
                    >
                      <SelectTrigger id="planner_provider">
                        <SelectValue placeholder="プロバイダーを選択" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={PlannerProviderEnum.OPENAI}>OpenAI</SelectItem>
                        <SelectItem value={PlannerProviderEnum.ANTHROPIC}>Anthropic</SelectItem>
                        <SelectItem value={PlannerProviderEnum.GROQ}>Groq</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="planner_model">プランナーモデル</Label>
                    <Select 
                      defaultValue={config.planner_model}
                      onValueChange={(value) => updateConfig({ planner_model: value })}
                      disabled={isPending}
                    >
                      <SelectTrigger id="planner_model">
                        <SelectValue placeholder="モデルを選択" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                        <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="writer_provider">ライタープロバイダー</Label>
                    <Select 
                      defaultValue={config.writer_provider}
                      onValueChange={(value) => updateConfig({ 
                        writer_provider: value as WriterProviderEnum 
                      })}
                      disabled={isPending}
                    >
                      <SelectTrigger id="writer_provider">
                        <SelectValue placeholder="プロバイダーを選択" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={WriterProviderEnum.OPENAI}>OpenAI</SelectItem>
                        <SelectItem value={WriterProviderEnum.ANTHROPIC}>Anthropic</SelectItem>
                        <SelectItem value={WriterProviderEnum.GROQ}>Groq</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>
              
              {/* 検索設定セクション */}
              <Card className="border-gray-200">
                <CardHeader className="pb-3 pt-4">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Search size={16} />
                    検索設定
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 pt-0">
                  <div className="space-y-2">
                    <Label htmlFor="search_provider">検索プロバイダー</Label>
                    <Select 
                      defaultValue={config.default_search_provider}
                      onValueChange={(value) => updateConfig({ 
                        default_search_provider: value as SearchProviderEnum 
                      })}
                      disabled={isPending}
                    >
                      <SelectTrigger id="search_provider">
                        <SelectValue placeholder="プロバイダーを選択" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={SearchProviderEnum.TAVILY}>Tavily</SelectItem>
                        <SelectItem value={SearchProviderEnum.ARXIV}>arXiv</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-4">
                    <Label className="mb-1 block">クエリ数</Label>
                    <div className="flex items-center gap-4">
                      <Slider 
                        defaultValue={[config.number_of_queries || 2]} 
                        min={1} 
                        max={5} 
                        step={1} 
                        className="flex-1"
                        onValueChange={(values) => updateConfig({ number_of_queries: values[0] })}
                        disabled={isPending}
                      />
                      <span className="text-sm font-medium">{config.number_of_queries || 2}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              {/* 詳細リサーチ設定セクション */}
              <Card className="border-gray-200">
                <CardHeader className="pb-3 pt-4">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Layers size={16} />
                    詳細リサーチ設定
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 pt-0">
                  <div className="space-y-4">
                    <Label className="mb-1 block">深さ</Label>
                    <div className="flex items-center gap-4">
                      <Slider 
                        defaultValue={[config.deep_research_depth || 1]} 
                        min={1} 
                        max={3} 
                        step={1} 
                        className="flex-1"
                        onValueChange={(values) => updateConfig({ deep_research_depth: values[0] })}
                        disabled={isPending || !config.enable_deep_research}
                      />
                      <span className="text-sm font-medium">{config.deep_research_depth || 1}</span>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <Label className="mb-1 block">幅</Label>
                    <div className="flex items-center gap-4">
                      <Slider 
                        defaultValue={[config.deep_research_breadth || 2]} 
                        min={1} 
                        max={5} 
                        step={1} 
                        className="flex-1"
                        onValueChange={(values) => updateConfig({ deep_research_breadth: values[0] })}
                        disabled={isPending || !config.enable_deep_research}
                      />
                      <span className="text-sm font-medium">{config.deep_research_breadth || 2}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="flex justify-end gap-4">
        <Button 
          variant="outline" 
          type="button"
          onClick={() => resetForm()}
          disabled={isPending}
        >
          リセット
        </Button>
        <Button 
          type="submit" 
          className="bg-blue-600 hover:bg-blue-700"
          disabled={isPending}
        >
          {isPending ? 'リサーチを開始中...' : 'リサーチを開始'}
        </Button>
      </div>
    </form>
  );
}