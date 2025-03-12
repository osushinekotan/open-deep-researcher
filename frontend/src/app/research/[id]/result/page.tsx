import { Suspense } from 'react';
import { ResultClient } from './result-client';
import { Loader2 } from 'lucide-react';

// params が Promise<{ id: string }> として渡される場合の修正例
export default async function ResultPage({ params }: { params: Promise<{ id: string }> }) {
  // params を await してから id を取得する
  const { id: researchId } = await params;
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-[70vh]">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
      </div>
    }>
      <ResultClient researchId={researchId} />
    </Suspense>
  );
}
