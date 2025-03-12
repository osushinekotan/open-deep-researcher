import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { 
  ArrowDownToLine, 
  Printer, 
  Share2, 
  BookOpen,
  Menu,
  Clock,
  ExternalLink
} from 'lucide-react';
import {
  Sheet,
  SheetContent,
  SheetTrigger,
} from '@/components/ui/sheet';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { formatDate } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';

interface Section {
  id: string;
  title: string;
  content: string;
}

interface Reference {
  id: string;
  title: string;
  authors: string;
  year: string;
  url: string;
}

interface ReportViewerProps {
  topic: string;
  createdAt: string;
  completedAt: string;
  sections: Section[];
  references?: Reference[];
}

export function ReportViewer({ 
  topic, 
  createdAt, 
  completedAt, 
  sections, 
  references = [] 
}: ReportViewerProps) {
  const [activeSection, setActiveSection] = useState(sections[0]?.id);

  return (
    <div className="min-h-screen flex flex-col">
      {/* ヘッダー部分 - 幅を修正し背景色を変更 */}
      <div className="bg-white border-b sticky top-0 z-10 py-4 w-full">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-end items-center">
          {/* <div className="font-semibold">Research Report</div> */}
          
          <div className="flex gap-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="outline" size="icon">
                    <Printer size={16} />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>印刷</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="outline" size="icon">
                    <ArrowDownToLine size={16} />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>ダウンロード</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="outline" size="icon">
                    <Share2 size={16} />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>共有</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="outline" size="icon" className="md:hidden">
                  <Menu size={16} />
                </Button>
              </SheetTrigger>
              <SheetContent side="right">
                <div className="py-4">
                  <h3 className="font-semibold mb-4">目次</h3>
                  <nav className="space-y-2">
                    {sections.map(section => (
                      <button
                        key={section.id}
                        onClick={() => setActiveSection(section.id)}
                        className={`block w-full text-left px-2 py-1.5 rounded text-sm ${
                          activeSection === section.id 
                            ? 'bg-blue-50 text-blue-700 font-medium' 
                            : 'hover:bg-gray-50'
                        }`}
                      >
                        {section.title}
                      </button>
                    ))}
                  </nav>
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 pt-8 flex-grow grid grid-cols-1 md:grid-cols-4 gap-8">
        {/* サイドバー: 目次 */}
        <div className="hidden md:block md:col-span-1">
          <div className="sticky top-24">
            <div className="mb-4">
              <Badge className="bg-green-500 mb-2">完了</Badge>
              <h2 className="font-semibold text-gray-500 text-sm flex items-center gap-1.5 mb-2">
                <Clock size={14} />
                <span>完了日: {formatDate(completedAt)}</span>
              </h2>
            </div>
            
            <h3 className="font-semibold mb-3 flex items-center gap-1.5">
              <BookOpen size={16} />
              <span>目次</span>
            </h3>
            
            <nav className="space-y-2">
              {sections.map(section => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`block w-full text-left px-3 py-2 rounded text-sm ${
                    activeSection === section.id 
                      ? 'bg-blue-50 text-blue-700 font-medium' 
                      : 'hover:bg-gray-50'
                  }`}
                >
                  {section.title}
                </button>
              ))}
            </nav>
          </div>
        </div>
        
        {/* メインコンテンツ - Markdownレンダリングを追加 */}
        <div className="md:col-span-3">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">{topic}</h1>
            <p className="text-gray-500">作成日: {formatDate(createdAt)}</p>
          </div>
          
          <div className="prose prose-lg max-w-none">
            {sections.map(section => (
              <div key={section.id} id={section.id} className="mb-12">
                <h2 className="text-2xl font-bold mb-4">{section.title}</h2>
                {/* Markdownレンダリングを実装 - wrapperで囲む形に修正 */}
                <div className="prose max-w-none">
                <ReactMarkdown
                  components={{
                    a: ({node, ...props}) => (
                      <a {...props} className="text-blue-600 hover:underline" />
                    )
                  }}
                >
                  {section.content}
                </ReactMarkdown>
                </div>
              </div>
            ))}
            
            {references.length > 0 && (
              <>
                <Separator className="my-8" />
                
                <div>
                  <h2 className="text-2xl font-bold mb-4">参考文献</h2>
                  <ul className="space-y-4">
                    {references.map(ref => (
                      <li key={ref.id} className="flex items-start">
                        <div className="flex-1">
                          <p className="font-medium">{ref.title}</p>
                          <p className="text-sm text-gray-600">{ref.authors} ({ref.year})</p>
                        </div>
                        <a 
                          href={ref.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 flex items-center ml-2"
                        >
                          <ExternalLink size={14} />
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}