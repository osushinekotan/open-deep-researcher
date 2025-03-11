// これはサーバーコンポーネント
import { ResultClient } from './result-client';

// サーバーコンポーネントでパラメータを取得して、
// クライアントコンポーネントに単純なプロパティとして渡す
export default function ResultPage({ params }: { params: { id: string } }) {
  return <ResultClient researchId={params.id} />;
}