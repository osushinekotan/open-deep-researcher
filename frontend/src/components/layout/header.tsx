"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { MainNav } from "./main-nav";
import { Button } from "@/components/ui/button";
import { Plus, LogIn, LogOut, User } from "lucide-react";
import { useAuthStore } from "@/store/auth-store";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function Header() {
  const router = useRouter();
  const { isAuthenticated, username, logout } = useAuthStore();

  const handleLogout = () => {
    console.log("ログアウト処理を実行");
    logout();
    // 明示的にホームページに遷移
    router.push('/home');
  };

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
        <div className="flex items-center gap-4">
          {isAuthenticated ? (
            <>
              <Link href="/new-research">
                <Button className="gap-1.5 bg-blue-600 hover:bg-blue-700 shadow-sm">
                  <Plus size={16} />
                  <span>New Research</span>
                </Button>
              </Link>
              
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" className="gap-1.5">
                    <User size={16} />
                    <span>{username}</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={handleLogout} className="text-red-600 cursor-pointer">
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>ログアウト</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          ) : (
            <Link href="/login">
              <Button variant="outline" className="gap-1.5">
                <LogIn size={16} />
                <span>ログイン</span>
              </Button>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}