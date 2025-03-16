"use client";

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
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
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
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Label } from '@/components/ui/label';
import { 
  Info, 
  Rocket, 
  Settings, 
  Search, 
  Layers, 
  FileText, 
  Globe, 
  Database, 
  Cpu, 
  HelpCircle, 
  Zap,
  BookOpen,
  AlertCircle,
  Workflow
} from 'lucide-react';
import { useResearchStore } from '@/store/research-store';
import { useStartResearch } from '@/hooks/use-research';
import { 
  PlannerProviderEnum, 
  WriterProviderEnum, 
  SearchProviderEnum 
} from '@/types/api';

import { useAuthStore } from "@/store/auth-store";
import { useState, useEffect } from 'react';
import { documentService } from '@/services/document-service';

export function ResearchForm() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState('basic');
  
  // グローバルストアからフォーム状態を取得
  const { topic, config, setTopic, updateConfig, resetForm } = useResearchStore();
  
  // リサーチ開始ミューテーション
  const { mutate: startResearch, isPending } = useStartResearch();
  
  // ユーザー名を取得
  const { username } = useAuthStore();
  
  // 有効なファイル一覧を保持
  const [enabledFiles, setEnabledFiles] = useState<string[]>([]);
  
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

  // ツールチップのラッパーコンポーネント
  const InfoTooltip = ({ children, content }: { children: React.ReactNode, content: string }) => (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="inline-flex items-center cursor-help">
            {children}
            <HelpCircle className="ml-1 h-4 w-4 text-gray-400" />
          </div>
        </TooltipTrigger>
        <TooltipContent className="max-w-sm">
          <p>{content}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );

  // LLMモデルのオプション
  const modelOptions = {
    openai: [
      { value: 'gpt-4o', label: 'GPT-4o' },
      { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
      { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
    ],
    anthropic: [
      { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' },
      { value: 'claude-3-sonnet-20240229', label: 'Claude 3 Sonnet' },
      { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku' },
    ],
    groq: [
      { value: 'llama-3-8b-8192', label: 'LLaMA-3 8B' },
      { value: 'llama-3-70b-8192', label: 'LLaMA-3 70B' },
    ]
  };


  // ローカル検索が有効になったときにファイル一覧を取得
  useEffect(() => {
    async function fetchEnabledFiles() {
      if (config.available_search_providers?.includes(SearchProviderEnum.LOCAL)) {
        try {
          const documents = await documentService.listDocuments(username || undefined);
          const enabled = documents.filter(doc => doc.is_enabled).map(doc => doc.filename);
          setEnabledFiles(enabled);
          
          // ローカル検索設定に有効ファイルリストを反映
          updateConfig({
            local_search_config: {
              ...config.local_search_config,
              enabled_files: enabled,
            }
          });
        } catch (error) {
          console.error('Failed to fetch document list:', error);
        }
      }
    }
    
    fetchEnabledFiles();
  }, [config.available_search_providers, username]);

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      <Card>
        <CardHeader>
          <CardTitle className="text-xl flex items-center gap-2">
            <Rocket size={20} />
            Research Topic
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
                "?" をつけることで質問として解釈され、その回答をリサーチします
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="basic" className="space-y-6" value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-4 max-w-4xl mx-auto">
          <TabsTrigger value="basic" className="flex items-center gap-1.5">
            <Settings size={16} />
            <span>基本設定</span>
          </TabsTrigger>
          <TabsTrigger value="report" className="flex items-center gap-1.5">
            <FileText size={16} />
            <span>レポート設定</span>
          </TabsTrigger>
          <TabsTrigger value="models" className="flex items-center gap-1.5">
            <Cpu size={16} />
            <span>モデル設定</span>
          </TabsTrigger>
          <TabsTrigger value="search" className="flex items-center gap-1.5">
            <Search size={16} />
            <span>検索設定</span>
          </TabsTrigger>
        </TabsList>
        
        {/* 基本設定タブ */}
        <TabsContent value="basic">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">基本設定</CardTitle>
              <CardDescription>
                リサーチの基本的な動作と実行方法を設定します
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* 言語設定 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <Label className="text-base font-medium">言語設定</Label>
                    <RadioGroup 
                      defaultValue={config.language || "japanese"}
                      onValueChange={(value) => updateConfig({ language: value })}
                      className="flex flex-col space-y-1"
                    >
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="japanese" id="lang-jp" />
                        <Label htmlFor="lang-jp" className="font-normal flex items-center">
                          <Globe className="mr-1.5 h-4 w-4" /> 日本語
                        </Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="english" id="lang-en" />
                        <Label htmlFor="lang-en" className="font-normal flex items-center">
                          <Globe className="mr-1.5 h-4 w-4" /> English
                        </Label>
                      </div>
                    </RadioGroup>
                  </div>
                </div>
                {/* Deep Researchと認証設定 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <div className="bg-gray-50 p-4 rounded-lg border">
                      <div className="flex justify-between items-start mb-2">
                        <InfoTooltip content="より詳細で深い分析を行います。複雑なトピックには推奨ですが、実行時間が長くなります。">
                          <Label className="font-medium text-base">Deep Research を有効化</Label>
                        </InfoTooltip>
                        <Switch 
                          id="deep_research" 
                          checked={config.enable_deep_research}
                          onCheckedChange={(checked) => updateConfig({ enable_deep_research: checked })}
                          disabled={isPending}
                        />
                      </div>
                      <p className="text-sm text-gray-600">
                        探索的リサーチを実行し、見つかった情報から更に検索を行います
                      </p>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="bg-gray-50 p-4 rounded-lg border">
                      <div className="flex justify-between items-start mb-2">
                        <InfoTooltip content="有効にすると、リサーチプランの確認をスキップして自動的に実行します。無効にするとプランを確認してフィードバックを提供できます。">
                          <Label className="font-medium text-base">フィードバックをスキップ</Label>
                        </InfoTooltip>
                        <Switch 
                          id="skip_feedback" 
                          checked={config.skip_human_feedback}
                          onCheckedChange={(checked) => updateConfig({ skip_human_feedback: checked })}
                          disabled={isPending}
                        />
                      </div>
                      <p className="text-sm text-gray-600">
                        リサーチプランの確認をスキップして自動的に実行します
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        {/* レポート設定タブ */}
        <TabsContent value="report">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">レポート設定</CardTitle>
              <CardDescription>
                生成されるレポートの形式や内容に関する設定を行います
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* レポート形式 */}
              <div className="grid grid-cols-1 gap-6">
                <div className="space-y-3">
                  <InfoTooltip content="レポートにどのようなセクションを含むか指定します。デフォルトはトピックに基づいて自動的に構成します。">
                    <Label className="text-base font-medium">レポート構造</Label>
                  </InfoTooltip>
                  <Select 
                    defaultValue={config.report_structure ? "custom" : "auto"}
                    onValueChange={(value) => {
                      if (value === "custom") {
                        updateConfig({ 
                          report_structure: "Use this structure to create a report on the user-provided topic:\nMain Body Sections:\n   - Each section should focus on a sub-topic of the user-provided topic\n   - if user provided question, you should make critical sections to answer the question\n   - Do not include introduction or conclusion"
                        });
                      } else {
                        updateConfig({ report_structure: undefined });
                      }
                    }}
                    disabled={isPending}
                  >
                    <SelectTrigger id="report_format" className="w-full">
                      <SelectValue placeholder="レポート形式を選択" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="auto">自動（推奨）</SelectItem>
                      <SelectItem value="custom">カスタム</SelectItem>
                    </SelectContent>
                  </Select>

                  {(config.report_structure || config.report_structure === "") && (
                    <Textarea
                      placeholder="レポート構造のカスタム指示（マークダウン形式）"
                      className="mt-2 h-24"
                      value={config.report_structure || ""}
                      onChange={(e) => updateConfig({ report_structure: e.target.value })}
                      disabled={isPending}
                    />
                  )}
                </div>
              </div>

              {/* 単語数制限 */}
              <div className="space-y-3">
                <InfoTooltip content="レポートの各セクションの最大単語数を設定します。長すぎると読みにくくなりますが、短すぎると情報が不足する可能性があります。">
                  <Label className="text-base font-medium">単語数制限</Label>
                </InfoTooltip>
                {/* セクション最大数を追加 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3 md:col-span-2">
                    <Label className="text-sm">セクション最大数</Label>
                    <div className="flex items-center gap-4">
                      <Slider 
                        defaultValue={[config.max_sections || 5]} 
                        min={2} 
                        max={10} 
                        step={1} 
                        className="flex-1"
                        onValueChange={(values) => updateConfig({ max_sections: values[0] })}
                        disabled={isPending}
                      />
                      <span className="text-sm font-medium w-12 text-right">{config.max_sections || 5}</span>
                    </div>
                    <p className="text-xs text-gray-500">レポートに含めるセクションの最大数</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <Label className="text-sm">セクション最大単語数</Label>
                    <div className="flex items-center gap-4">
                      <Slider 
                        defaultValue={[config.max_section_words || 1000]} 
                        min={500} 
                        max={2000} 
                        step={100} 
                        className="flex-1"
                        onValueChange={(values) => updateConfig({ max_section_words: values[0] })}
                        disabled={isPending}
                      />
                      <span className="text-sm font-medium w-12 text-right">{config.max_section_words || 1000}</span>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <Label className="text-sm">サブセクション最大単語数</Label>
                    <div className="flex items-center gap-4">
                      <Slider 
                        defaultValue={[config.max_subsection_words || 500]} 
                        min={200} 
                        max={1000} 
                        step={50} 
                        className="flex-1"
                        onValueChange={(values) => updateConfig({ max_subsection_words: values[0] })}
                        disabled={isPending}
                      />
                      <span className="text-sm font-medium w-12 text-right">{config.max_subsection_words || 500}</span>
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                  <div className="space-y-3">
                    <Label className="text-sm">序論最大単語数</Label>
                    <div className="flex items-center gap-4">
                      <Slider 
                        defaultValue={[config.max_introduction_words || 500]} 
                        min={200} 
                        max={1000} 
                        step={50} 
                        className="flex-1"
                        onValueChange={(values) => updateConfig({ max_introduction_words: values[0] })}
                        disabled={isPending}
                      />
                      <span className="text-sm font-medium w-12 text-right">{config.max_introduction_words || 500}</span>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <Label className="text-sm">結論最大単語数</Label>
                    <div className="flex items-center gap-4">
                      <Slider 
                        defaultValue={[config.max_conclusion_words || 500]} 
                        min={200} 
                        max={1000} 
                        step={50} 
                        className="flex-1"
                        onValueChange={(values) => updateConfig({ max_conclusion_words: values[0] })}
                        disabled={isPending}
                      />
                      <span className="text-sm font-medium w-12 text-right">{config.max_conclusion_words || 500}</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        {/* モデル設定タブ */}
        <TabsContent value="models">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">AI モデル設定</CardTitle>
              <CardDescription>
                リサーチで使用するAIモデルの詳細設定を行います
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* プランナーモデル設定 */}
              <Accordion type="single" collapsible defaultValue="planner" className="w-full">
                <AccordionItem value="planner" className="border-b">
                  <AccordionTrigger className="py-4 hover:no-underline">
                    <div className="flex items-center gap-2 text-base font-medium">
                      <Workflow size={16} /> 
                      <span>プランナーモデル設定</span>
                      <InfoTooltip content="リサーチプランの生成と全体の戦略を担当するAIモデルを設定します。より高度なモデルを使用すると質の高いプランが生成されますが、実行時間が長くなります。">
                        <span></span>
                      </InfoTooltip>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="py-3 space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-3">
                        <Label htmlFor="planner_provider">プロバイダー</Label>
                        <Select 
                          defaultValue={config.planner_provider || PlannerProviderEnum.OPENAI}
                          onValueChange={(value: PlannerProviderEnum) => updateConfig({ planner_provider: value })}
                          disabled={isPending}
                        >
                          <SelectTrigger id="planner_provider">
                            <SelectValue placeholder="プロバイダーを選択" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value={PlannerProviderEnum.OPENAI}>OpenAI</SelectItem>
                            {/* <SelectItem value={PlannerProviderEnum.ANTHROPIC}>Anthropic</SelectItem>
                            <SelectItem value={PlannerProviderEnum.GROQ}>Groq</SelectItem> */}
                          </SelectContent>
                        </Select>
                      </div>
                      
                      <div className="space-y-3">
                        <Label htmlFor="planner_model">モデル</Label>
                        <Select 
                          defaultValue={config.planner_model || "gpt-4o"}
                          onValueChange={(value) => updateConfig({ planner_model: value })}
                          disabled={isPending}
                        >
                          <SelectTrigger id="planner_model">
                            <SelectValue placeholder="モデルを選択" />
                          </SelectTrigger>
                          <SelectContent>
                            {modelOptions[config.planner_provider as keyof typeof modelOptions]?.map((model) => (
                              <SelectItem key={model.value} value={model.value}>{model.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <Label htmlFor="max_planner_tokens">最大トークン数</Label>
                      <div className="flex items-center gap-4">
                        <Slider 
                          defaultValue={[(config.planner_model_config?.max_tokens as number) || 4096]} 
                          min={1024} 
                          max={16384} 
                          step={1024} 
                          className="flex-1"
                          onValueChange={(values) => updateConfig({ 
                            planner_model_config: { 
                              ...config.planner_model_config,
                              max_tokens: values[0] 
                            } 
                          })}
                          disabled={isPending}
                        />
                        <span className="text-sm font-medium w-16 text-right">{(config.planner_model_config?.max_tokens as number) || 4096}</span>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
                
                {/* ライターモデル設定 */}
                <AccordionItem value="writer" className="border-b">
                  <AccordionTrigger className="py-4 hover:no-underline">
                    <div className="flex items-center gap-2 text-base font-medium">
                      <FileText size={16} /> 
                      <span>ライターモデル設定</span>
                      <InfoTooltip content="セクションの執筆を担当するAIモデルを設定します。質の高い文章を生成するには高度なモデルが必要です。">
                        <span></span>
                      </InfoTooltip>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="py-3 space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-3">
                        <Label htmlFor="writer_provider">プロバイダー</Label>
                        <Select 
                          defaultValue={config.writer_provider || WriterProviderEnum.OPENAI}
                          onValueChange={(value: WriterProviderEnum) => updateConfig({ writer_provider: value })}
                          disabled={isPending}
                        >
                          <SelectTrigger id="writer_provider">
                            <SelectValue placeholder="プロバイダーを選択" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value={WriterProviderEnum.OPENAI}>OpenAI</SelectItem>
                            {/* <SelectItem value={WriterProviderEnum.ANTHROPIC}>Anthropic</SelectItem>
                            <SelectItem value={WriterProviderEnum.GROQ}>Groq</SelectItem> */}
                          </SelectContent>
                        </Select>
                      </div>
                      
                      <div className="space-y-3">
                        <Label htmlFor="writer_model">モデル</Label>
                        <Select 
                          defaultValue={config.writer_model || "gpt-4o"}
                          onValueChange={(value) => updateConfig({ writer_model: value })}
                          disabled={isPending}
                        >
                          <SelectTrigger id="writer_model">
                            <SelectValue placeholder="モデルを選択" />
                          </SelectTrigger>
                          <SelectContent>
                            {modelOptions[config.writer_provider as keyof typeof modelOptions]?.map((model) => (
                              <SelectItem key={model.value} value={model.value}>{model.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <Label htmlFor="max_writer_tokens">最大トークン数</Label>
                      <div className="flex items-center gap-4">
                        <Slider 
                          defaultValue={[(config.writer_model_config?.max_tokens as number) || 8192]} 
                          min={1024} 
                          max={32768} 
                          step={1024} 
                          className="flex-1"
                          onValueChange={(values) => updateConfig({ 
                            writer_model_config: { 
                              ...config.writer_model_config,
                              max_tokens: values[0] 
                            } 
                          })}
                          disabled={isPending}
                        />
                        <span className="text-sm font-medium w-16 text-right">{(config.writer_model_config?.max_tokens as number) || 8192}</span>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
                
                {/* 結論ライターモデル設定 */}
                <AccordionItem value="conclusion" className="border-b">
                  <AccordionTrigger className="py-4 hover:no-underline">
                    <div className="flex items-center gap-2 text-base font-medium">
                      <BookOpen size={16} /> 
                      <span>結論ライターモデル設定</span>
                      <InfoTooltip content="結論を生成するためのAIモデルを設定します。結論はレポート全体をまとめる重要なセクションです。また、ユーザーの質問に対する最終的な回答を行います">
                        <span></span>
                      </InfoTooltip>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="py-3 space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-3">
                        <Label htmlFor="conclusion_writer_provider">プロバイダー</Label>
                        <Select 
                          defaultValue={config.conclusion_writer_provider || WriterProviderEnum.OPENAI}
                          onValueChange={(value: WriterProviderEnum) => updateConfig({ conclusion_writer_provider: value })}
                          disabled={isPending}
                        >
                          <SelectTrigger id="conclusion_writer_provider">
                            <SelectValue placeholder="プロバイダーを選択" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value={WriterProviderEnum.OPENAI}>OpenAI</SelectItem>
                            {/* <SelectItem value={WriterProviderEnum.ANTHROPIC}>Anthropic</SelectItem>
                            <SelectItem value={WriterProviderEnum.GROQ}>Groq</SelectItem> */}
                          </SelectContent>
                        </Select>
                      </div>
                      
                      <div className="space-y-3">
                        <Label htmlFor="conclusion_writer_model">モデル</Label>
                        <Select 
                          defaultValue={config.conclusion_writer_model || "gpt-3.5-turbo"}
                          onValueChange={(value) => updateConfig({ conclusion_writer_model: value })}
                          disabled={isPending}
                        >
                          <SelectTrigger id="conclusion_writer_model">
                            <SelectValue placeholder="モデルを選択" />
                          </SelectTrigger>
                          <SelectContent>
                            {modelOptions[config.conclusion_writer_provider as keyof typeof modelOptions]?.map((model) => (
                              <SelectItem key={model.value} value={model.value}>{model.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardContent>
          </Card>
        </TabsContent>
        
        {/* 検索設定タブ */}
        <TabsContent value="search">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">検索設定</CardTitle>
              <CardDescription>
                情報収集のための検索設定をカスタマイズします
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* 検索プロバイダー設定 */}
              <div className="space-y-3">
                <InfoTooltip content="使用可能な検索プロバイダーを選択します。異なる情報源からの検索結果を組み合わせることで、より包括的な調査が可能になります。">
                  <Label className="text-base font-medium">検索プロバイダー</Label>
                </InfoTooltip>
                <div className="border rounded-lg p-4 bg-gray-50 space-y-3">
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
                    <Label htmlFor="search_tavily" className="font-medium flex items-center gap-1.5">
                      <Search size={14} />
                      Tavily
                      <span className="text-xs font-normal text-gray-500">(汎用ウェブ検索)</span>
                    </Label>
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
                    <Label htmlFor="search_arxiv" className="font-medium flex items-center gap-1.5">
                      <Database size={14} />
                      arXiv
                      <span className="text-xs font-normal text-gray-500">(学術論文検索)</span>
                    </Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Checkbox 
                      id="search_local" 
                      checked={config.available_search_providers?.includes(SearchProviderEnum.LOCAL)}
                      onCheckedChange={(checked) => {
                        const providers = [...(config.available_search_providers || [])];
                        if (checked) {
                          if (!providers.includes(SearchProviderEnum.LOCAL)) {
                            providers.push(SearchProviderEnum.LOCAL);
                          }
                        } else {
                          const index = providers.indexOf(SearchProviderEnum.LOCAL);
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
                    <Label htmlFor="search_local" className="font-medium flex items-center gap-1.5">
                      <Database size={14} />
                      ローカルドキュメント
                      <span className="text-xs font-normal text-gray-500">(アップロード済みファイル)</span>
                    </Label>
                  </div>

                </div>
                <p className="text-xs text-gray-500 mt-1">少なくとも1つの検索プロバイダーを選択してください</p>
              </div>
              {config.available_search_providers && config.available_search_providers.length > 0 && (
                <Accordion type="single" collapsible defaultValue="provider-settings" className="w-full border rounded-lg overflow-hidden">
                  <AccordionItem value="provider-settings" className="border-none">
                    <AccordionTrigger className="px-4 py-3 hover:no-underline bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-2 text-base font-medium">
                        <Settings size={16} /> 
                        <span>検索プロバイダー詳細設定</span>
                        <InfoTooltip content="各検索プロバイダーの詳細設定を行います。最大取得件数や追加機能を設定できます。">
                          <span></span>
                        </InfoTooltip>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="pt-3 pb-1 px-4 space-y-6 bg-white">
                      {/* Tavily設定 */}
                      {config.available_search_providers.includes(SearchProviderEnum.TAVILY) && (
                        <div className="p-4 space-y-3">
                          <h4 className="font-medium text-sm flex items-center gap-1.5">
                            <Search size={14} />
                            Tavily 設定
                          </h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2 md:col-span-2">
                              <Label htmlFor="tavily_max_results" className="text-sm">最大取得件数</Label>
                              <div className="flex items-center gap-4">
                                <Slider 
                                  id="tavily_max_results"
                                  defaultValue={[config.tavily_search_config?.max_results || 5]} 
                                  min={1} 
                                  max={10} 
                                  step={1} 
                                  className="flex-1"
                                  onValueChange={(values) => updateConfig({ 
                                    tavily_search_config: { 
                                      ...config.tavily_search_config,
                                      max_results: values[0] 
                                    } 
                                  })}
                                  disabled={isPending}
                                />
                                <span className="text-sm font-medium w-8 text-right">{config.tavily_search_config?.max_results || 5}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* arXiv設定 */}
                      {config.available_search_providers.includes(SearchProviderEnum.ARXIV) && (
                        <div className=" p-4 space-y-3">
                          <h4 className="font-medium text-sm flex items-center gap-1.5">
                            <Database size={14} />
                            arXiv 設定
                          </h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2 md:col-span-2">
                              <Label htmlFor="arxiv_max_docs" className="text-sm">最大取得論文数</Label>
                              <div className="flex items-center gap-4">
                                <Slider 
                                  id="arxiv_max_docs"
                                  defaultValue={[config.arxiv_search_config?.load_max_docs || 5]} 
                                  min={1} 
                                  max={10} 
                                  step={1} 
                                  className="flex-1"
                                  onValueChange={(values) => updateConfig({ 
                                    arxiv_search_config: { 
                                      ...config.arxiv_search_config,
                                      load_max_docs: values[0] 
                                    } 
                                  })}
                                  disabled={isPending}
                                />
                                <span className="text-sm font-medium w-8 text-right">{config.arxiv_search_config?.load_max_docs || 5}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* ローカルドキュメント設定 */}
                      {config.available_search_providers?.includes(SearchProviderEnum.LOCAL) && (
                        <div className="p-4 space-y-3">
                          <h4 className="font-medium text-sm flex items-center gap-1.5">
                            <Database size={14} />
                            ローカルドキュメント設定
                          </h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

                          <div className="space-y-2 md:col-span-2">
                              <Label htmlFor="local_top_k" className="text-sm">最大取得件数</Label>
                              <div className="flex items-center gap-4">
                                <Slider 
                                  id="local_top_k"
                                  defaultValue={[config.local_search_config?.top_k || 5]} 
                                  min={1} 
                                  max={10} 
                                  step={1} 
                                  className="flex-1"
                                  onValueChange={(values) => updateConfig({ 
                                    local_search_config: { 
                                      ...config.local_search_config,
                                      top_k: values[0] 
                                    } 
                                  })}
                                  disabled={isPending}
                                />
                                <span className="text-sm font-medium w-16 text-right">
                                  {config.local_search_config?.top_k || 5}
                                </span>
                              </div>
                            </div>


                            <div className="space-y-2 md:col-span-2">
                              <Label htmlFor="local_chunk_size" className="text-sm">チャンクサイズ</Label>
                              <div className="flex items-center gap-4">
                                <Slider 
                                  id="local_chunk_size"
                                  defaultValue={[config.local_search_config?.chunk_size || 10000]} 
                                  min={1000} 
                                  max={20000} 
                                  step={1000} 
                                  className="flex-1"
                                  onValueChange={(values) => updateConfig({ 
                                    local_search_config: { 
                                      ...config.local_search_config,
                                      chunk_size: values[0] 
                                    } 
                                  })}
                                  disabled={isPending}
                                />
                                <span className="text-sm font-medium w-16 text-right">
                                  {config.local_search_config?.chunk_size || 10000}
                                </span>
                              </div>
                            </div>
                            
                            <div className="space-y-2 md:col-span-2">
                              <Label htmlFor="local_chunk_overlap" className="text-sm">オーバーラップ</Label>
                              <div className="flex items-center gap-4">
                                <Slider 
                                  id="local_chunk_overlap"
                                  defaultValue={[config.local_search_config?.chunk_overlap || 2000]} 
                                  min={0} 
                                  max={5000} 
                                  step={500} 
                                  className="flex-1"
                                  onValueChange={(values) => updateConfig({ 
                                    local_search_config: { 
                                      ...config.local_search_config,
                                      chunk_overlap: values[0] 
                                    } 
                                  })}
                                  disabled={isPending}
                                />
                                <span className="text-sm font-medium w-16 text-right">
                                  {config.local_search_config?.chunk_overlap || 2000}
                                </span>
                              </div>
                            </div>
                          </div>
                          <div className="bg-blue-50 p-3 rounded-md flex items-start gap-2 text-sm">
                            <AlertCircle className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                            <div>
                              <p className="text-blue-700">使用するファイルは「ドキュメント管理」ページで設定できます。</p>
                              <a href="/documents" className="text-blue-600 mt-1 inline-block hover:text-blue-800 underline">
                                ドキュメント管理ページを開く
                              </a>
                            </div>
                          </div>
                          {/* 有効なファイル一覧を表示 */}
                          {enabledFiles.length > 0 && (
                            <div className="mt-2 p-3 bg-blue-50 rounded-md">
                              <p className="text-sm font-medium text-blue-700 mb-1">使用するファイル ({enabledFiles.length}件)</p>
                              <ul className="text-xs text-blue-600 space-y-1 pl-5 list-disc">
                                {enabledFiles.map(file => (
                                  <li key={file}>{file}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                      </AccordionContent>
                  </AccordionItem>
                </Accordion>
              )}
              {/* デフォルト検索プロバイダー設定 */}
              {config.available_search_providers && config.available_search_providers.length > 0 && (
                <div className="space-y-3">
                  <InfoTooltip content="複数のプロバイダーが有効な場合、最初に使用するデフォルトのプロバイダーを選択します。">
                    <Label className="text-base font-medium">デフォルト検索プロバイダー</Label>
                  </InfoTooltip>
                  <Select 
                    defaultValue={config.default_search_provider || config.available_search_providers[0]}
                    onValueChange={(value: SearchProviderEnum) => updateConfig({ default_search_provider: value })}
                    disabled={isPending || !config.available_search_providers || config.available_search_providers.length === 0}
                  >
                    <SelectTrigger id="default_search_provider">
                      <SelectValue placeholder="デフォルトのプロバイダーを選択" />
                    </SelectTrigger>
                    <SelectContent>
                      {config.available_search_providers?.map((provider) => (
                        <SelectItem key={provider} value={provider}>
                          {provider === 'tavily' ? 'Tavily' : 
                           provider === 'arxiv' ? 'arXiv' : 
                           provider === 'local' ? 'ローカルドキュメント' :
                           provider}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              
              
              {/* クエリ数設定 */}
              <div className="space-y-3">
                <InfoTooltip content="各トピックに対して生成する検索クエリの数を指定します。多くのクエリを使用すると、より多様な情報を収集できますが、実行時間が長くなります。">
                  <Label className="text-base font-medium">クエリ数</Label>
                </InfoTooltip>
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
                  <span className="text-sm font-medium w-8 text-right">{config.number_of_queries || 2}</span>
                </div>
                <p className="text-xs text-gray-500">各トピックに対して生成する検索クエリの数（多いほど時間がかかる）</p>
              </div>

              {/* リフレクション設定 */}
              <div className="space-y-3">
                <Label className="text-base font-medium">リフレクション数</Label>
                <div className="flex items-center gap-4">
                  <Slider 
                    defaultValue={[config.max_reflection || 2]} 
                    min={0} 
                    max={3} 
                    step={1} 
                    className="flex-1"
                    onValueChange={(values) => updateConfig({ max_reflection: values[0] })}
                    disabled={isPending}
                  />
                  <span className="text-sm font-medium w-8 text-right">{config.max_reflection || 2}</span>
                </div>
                <p className="text-xs text-gray-500">セクションごとにレポートプランを遂行できているかを判定する最大数</p>
              </div>
              
              {/* Deep Research 設定 */}
              {config.enable_deep_research && (
                <div className="border rounded-lg p-4 bg-gray-50 space-y-4">
                  <div className="flex items-center">
                    <InfoTooltip content="Deep Researchの深さと幅を設定します。深さは「探索の連鎖の長さ」、幅は「各段階で探索する情報の量」を表します。">
                      <Label className="text-base font-medium">Deep Research 設定</Label>
                    </InfoTooltip>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <Label className="text-sm">探索の深さ</Label>
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
                        <span className="text-sm font-medium w-8 text-right">{config.deep_research_depth || 1}</span>
                      </div>
                      <p className="text-xs text-gray-500">探索の連鎖の長さ（高いほど深い分析）</p>
                    </div>
                    
                    <div className="space-y-3">
                      <Label className="text-sm">探索の幅</Label>
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
                        <span className="text-sm font-medium w-8 text-right">{config.deep_research_breadth || 2}</span>
                      </div>
                      <p className="text-xs text-gray-500">各段階で探索する情報の量</p>
                    </div>
                  </div>
                </div>
              )}

              {/* トークン制限設定 */}
              <div className="space-y-3">
                <InfoTooltip content="各情報源から抽出するトークン（単語や記号）の最大数を設定します。値を大きくすると情報量が増えますが、処理時間やモデルの制限に影響します。">
                  <Label className="text-base font-medium">トークン制限</Label>
                </InfoTooltip>
                <div className="flex items-center gap-4">
                  <Slider 
                    defaultValue={[config.max_tokens_per_source || 8192]} 
                    min={1024} 
                    max={16384} 
                    step={1024} 
                    className="flex-1"
                    onValueChange={(values) => updateConfig({ max_tokens_per_source: values[0] })}
                    disabled={isPending}
                  />
                  <span className="text-sm font-medium w-16 text-right">{config.max_tokens_per_source || 8192}</span>
                </div>
                <p className="text-xs text-gray-500">各情報源から抽出する最大トークン数</p>
              </div>
              {/* リクエスト遅延設定 - 追加 */}
              <div className="space-y-3">
                <InfoTooltip content="連続したAPIリクエスト間の遅延時間（秒）を指定します。APIレート制限に到達するのを防ぐために使用できます。">
                  <Label className="text-base font-medium">リクエスト遅延（秒）</Label>
                </InfoTooltip>
                <div className="flex items-center gap-4">
                  <Slider 
                    defaultValue={[config.request_delay || 1]} 
                    min={0} 
                    max={5} 
                    step={0.1} 
                    className="flex-1"
                    onValueChange={(values) => updateConfig({ request_delay: values[0] })}
                    disabled={isPending}
                  />
                  <span className="text-sm font-medium w-8 text-right">{config.request_delay || 0}</span>
                </div>
                <p className="text-xs text-gray-500">APIリクエスト間の遅延時間（秒）</p>
              </div>
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