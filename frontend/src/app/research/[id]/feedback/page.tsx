// frontend/src/app/research/[id]/feedback/page.tsx
import { Suspense } from 'react';
import { FeedbackClient } from './feedback-client';
import { Loader2 } from 'lucide-react';

export default async function FeedbackPage({ params }: { params: { id: string } }) {
  const { id: researchId } = await params;
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-[70vh]">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
      </div>
    }>
      <FeedbackClient researchId={researchId} />
    </Suspense>
  );
}