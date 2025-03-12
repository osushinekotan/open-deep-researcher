"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { SectionModel } from "@/types/api";
import { Check, Search } from "lucide-react";
import { useSubmitFeedback } from "@/hooks/use-feedback";
import { useResearchStatus } from "@/hooks/use-research";

interface FeedbackFormProps {
  researchId: string;
  sections: SectionModel[];
}

export function FeedbackForm({ researchId, sections }: FeedbackFormProps) {
  const [feedback, setFeedback] = useState("");
  const router = useRouter();
  
  const { data: research } = useResearchStatus(researchId);
  const { mutate: submitFeedback, isPending } = useSubmitFeedback(researchId);

  const handleSubmit = (approve: boolean) => {
    // 承認の場合は空の文字列を送信
    const feedbackText = approve ? undefined : feedback;
    
    submitFeedback(feedbackText, {
      onSuccess: () => {
        // 成功したらリサーチ詳細ページに戻る
        router.push(`/research/${researchId}`);
      },
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="font-medium mb-2">リサーチプラン - セクション構成</h3>
        <div className="space-y-4">
          {sections.map((section, index) => (
            <div key={index} className="p-4 bg-white rounded-md border">
              <h4 className="font-medium text-gray-900 mb-1">{section.name}</h4>
              <p className="text-sm text-gray-600 mb-2">{section.description}</p>
              
              {/* 検索オプションの表示 */}
              {section.search_options && Object.keys(section.search_options).length > 0 && (
                <div className="mt-3 pt-2 border-t border-gray-100">
                  <h5 className="text-xs font-medium text-gray-500 flex items-center gap-1.5 mb-1.5">
                    <Search size={12} />
                    検索オプション
                  </h5>
                  <div className="flex flex-wrap gap-1.5">
                    {Array.isArray(section.search_options) ? (
                      /* 配列の場合 */
                      section.search_options.map((option, i) => (
                        <Badge key={i} variant="outline" className="text-xs bg-blue-50">
                          {typeof option === 'string' ? option : JSON.stringify(option)}
                        </Badge>
                      ))
                    ) : (
                      /* オブジェクトの場合 */
                      Object.entries(section.search_options).map(([key, value], i) => (
                        <Badge key={i} variant="outline" className="text-xs bg-blue-50">
                          {key}: {typeof value === 'string' ? value : JSON.stringify(value)}
                        </Badge>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      <Separator />
      <div>
        <h3 className="font-medium mb-2">フィードバック</h3>
        <Textarea 
          placeholder="このリサーチプランへのフィードバックを入力してください。特定のセクションの追加や変更を提案できます。空白のままで承認することも可能です。" 
          className="min-h-32"
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          disabled={isPending}
        />
      </div>
      
      <div className="flex justify-end gap-3 pt-2">
        <Button 
          variant="outline" 
          className="border-yellow-500 text-yellow-700 hover:bg-yellow-100 hover:text-yellow-800"
          onClick={() => router.back()}
          disabled={isPending}
        >
          キャンセル
        </Button>
        <Button 
          className="bg-green-600 hover:bg-green-700 flex items-center gap-1"
          onClick={() => handleSubmit(true)}
          disabled={isPending}
        >
          <Check size={16} />
          <span>プランを承認</span>
        </Button>
      </div>
    </div>
  );
}