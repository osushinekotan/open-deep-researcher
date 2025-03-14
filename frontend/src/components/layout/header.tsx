import Link from "next/link";
import { MainNav } from "./main-nav";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex h-16 items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/home" className="font-semibold text-xl flex items-center">
            <span className="text-blue-600 mr-1">Open</span>
            <span className="text-gray-900">Deep Researcher</span>
          </Link>
          <MainNav />
        </div>
        <div>
          <Link href="/new-research">
            <Button className="gap-1.5 bg-blue-600 hover:bg-blue-700 shadow-sm">
              <Plus size={16} />
              <span>New Research</span>
            </Button>
          </Link>
        </div>
      </div>
    </header>
  );
}