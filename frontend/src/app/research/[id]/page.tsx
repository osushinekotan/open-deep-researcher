// frontend/src/app/research/[id]/page.tsx
import { Suspense } from 'react';
import { DetailClient } from './detail-client';
import { Loader2 } from 'lucide-react';

export default async function ResearchDetailPage({ params }: { params: { id: string } }) {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-[70vh]">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
      </div>
    }>
      <DetailClient researchId={params.id} />
    </Suspense>
  );
}