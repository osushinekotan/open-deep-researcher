// frontend/src/app/research/[id]/result/page.tsx を修正

import { Suspense } from 'react';
import { ResultClient } from './result-client';
import { Loader2 } from 'lucide-react';

// サーバーコンポーネントでは非同期処理が可能
export default async function ResultPage({ params }: { params: { id: string } }) {
  // Next.js App Routerでは、サーバーコンポーネントを非同期にすることでパラメータを安全に使用できます
  // このコンポーネントをasyncにすることで、paramsに関するエラーを解決
  
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-[70vh]">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
      </div>
    }>
      <ResultClient researchId={params.id} />
    </Suspense>
  );
}