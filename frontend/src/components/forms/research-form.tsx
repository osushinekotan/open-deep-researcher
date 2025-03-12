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
import { Checkbox } from '@/components/ui/checkbox';
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
            <CardContent>
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <Label htmlFor="language" className="text-base font-medium">言語設定</Label>
                    <Select 
                      defaultValue={config.language} 
                      onValueChange={(value) => updateConfig({ language: value })}
                      disabled={isPending}
                    >
                      <SelectTrigger id="language" className="w-full">
                        <SelectValue placeholder="言語を選択" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="japanese">日本語</SelectItem>
                        <SelectItem value="english">英語</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-3">
                    <Label htmlFor="deep_research" className="text-base font-medium">詳細なリサーチ</Label>
                    <div className="flex items-center justify-between bg-gray-50 p-4 rounded-md border">
                      <div>
                        <p className="font-medium">詳細なリサーチを有効化</p>
                        <p className="text-sm text-gray-500">より詳細で深い分析を行います</p>
                      </div>
                      <Switch 
                        id="deep_research" 
                        defaultChecked={config.enable_deep_research}
                        onCheckedChange={(checked) => updateConfig({ enable_deep_research: checked })}
                        disabled={isPending}
                      />
                    </div>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <Label htmlFor="skip_feedback" className="text-base font-medium">フィードバック設定</Label>
                  <div className="flex items-center justify-between bg-gray-50 p-4 rounded-md border">
                    <div>
                      <p className="font-medium">フィードバックをスキップ</p>
                      <p className="text-sm text-gray-500">プランの確認をスキップして自動的に実行</p>
                    </div>
                    <Switch 
                      id="skip_feedback" 
                      checked={config.skip_human_feedback}
                      onCheckedChange={(checked) => updateConfig({ skip_human_feedback: checked })}
                      disabled={isPending}
                    />
                  </div>
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
              {/* LLM設定セクション */}
              <Card className="border-gray-200">
                <CardHeader className="pb-3 pt-4">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Settings size={16} />
                    LLM設定
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 pt-0">
                  <div className="space-y-2">
                    <Label htmlFor="llm_provider">LLMプロバイダー</Label>
                    <Select 
                      defaultValue="openai" 
                      disabled={true}
                    >
                      <SelectTrigger id="llm_provider">
                        <SelectValue placeholder="プロバイダーを選択" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="openai">OpenAI</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-gray-500">現在OpenAIのみサポートしています</p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="llm_model">LLMモデル</Label>
                    <Select 
                      defaultValue={config.planner_model || "gpt-4o"}
                      onValueChange={(value) => {
                        // plannerとwriterの両方のモデルを同じ値に更新
                        updateConfig({ 
                          planner_model: value,
                          writer_model: value,
                          planner_provider: PlannerProviderEnum.OPENAI,
                          writer_provider: WriterProviderEnum.OPENAI
                        });
                      }}
                      disabled={isPending}
                    >
                      <SelectTrigger id="llm_model">
                        <SelectValue placeholder="モデルを選択" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                        <SelectItem value="gpt-4o-mini">GPT-4o Mini</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>
              
              {/* 検索設定セクション - マルチチョイスに変更 */}
              <Card className="border-gray-200">
                <CardHeader className="pb-3 pt-4">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Search size={16} />
                    検索設定
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 pt-0">
                  <div className="space-y-2">
                    <Label htmlFor="search_providers" className="block mb-2">検索プロバイダー</Label>
                    <div className="space-y-3 border rounded-md p-4 bg-gray-50">
                      <div className="flex items-center space-x-2">
                        <Checkbox 
                          id="search_tavily" 
                          checked={config.available_search_providers?.includes(SearchProviderEnum.TAVILY)}
                          onCheckedChange={(checked) => {
                            const providers = [...(config.available_search_providers || [])];
                            if (checked) {
                              if (!providers.includes(SearchProviderEnum.TAVILY)) {
                                providers.push(SearchProviderEnum.TAVILY);
                              }
                            } else {
                              const index = providers.indexOf(SearchProviderEnum.TAVILY);
                              if (index >= 0) {
                                providers.splice(index, 1);
                              }
                            }
                            updateConfig({ 
                              available_search_providers: providers,
                              default_search_provider: providers.length > 0 ? providers[0] : undefined
                            });
                          }}
                          disabled={isPending}
                        />
                        <label htmlFor="search_tavily" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                          Tavily
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox 
                          id="search_arxiv" 
                          checked={config.available_search_providers?.includes(SearchProviderEnum.ARXIV)}
                          onCheckedChange={(checked) => {
                            const providers = [...(config.available_search_providers || [])];
                            if (checked) {
                              if (!providers.includes(SearchProviderEnum.ARXIV)) {
                                providers.push(SearchProviderEnum.ARXIV);
                              }
                            } else {
                              const index = providers.indexOf(SearchProviderEnum.ARXIV);
                              if (index >= 0) {
                                providers.splice(index, 1);
                              }
                            }
                            updateConfig({ 
                              available_search_providers: providers,
                              default_search_provider: providers.length > 0 ? providers[0] : undefined
                            });
                          }}
                          disabled={isPending}
                        />
                        <label htmlFor="search_arxiv" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                          arXiv
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox 
                          id="search_patent" 
                          checked={config.available_search_providers?.includes(SearchProviderEnum.GOOGLE_PATENT)}
                          onCheckedChange={(checked) => {
                            const providers = [...(config.available_search_providers || [])];
                            if (checked) {
                              if (!providers.includes(SearchProviderEnum.GOOGLE_PATENT)) {
                                providers.push(SearchProviderEnum.GOOGLE_PATENT);
                              }
                            } else {
                              const index = providers.indexOf(SearchProviderEnum.GOOGLE_PATENT);
                              if (index >= 0) {
                                providers.splice(index, 1);
                              }
                            }
                            updateConfig({ 
                              available_search_providers: providers,
                              default_search_provider: providers.length > 0 ? providers[0] : undefined
                            });
                          }}
                          disabled={isPending}
                        />
                        <label htmlFor="search_patent" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                          Google Patent
                        </label>
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">複数選択可能です。少なくとも1つは選択してください。</p>
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