import { ResearchForm } from "@/components/forms/research-form";

export default function NewResearchPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <h1 className="text-3xl font-bold mb-2">Research</h1>
      <p className="text-gray-500 mb-8">リサーチトピックと設定をカスタマイズします</p>

      <ResearchForm />
    </div>
  );
}