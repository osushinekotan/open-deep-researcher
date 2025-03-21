"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { LayoutDashboard, Home, BookOpen, FileArchive } from "lucide-react";

export function MainNav() {
  const pathname = usePathname();
  
  const navItems = [
    {
      href: "/home",
      label: "ホーム",
      icon: <Home size={16} />,
      active: pathname === "/home",
    },
    {
      href: "/dashboard",
      label: "ダッシュボード",
      icon: <LayoutDashboard size={16} />,
      active: pathname === "/dashboard" || pathname === "/",
    },
    {
      href: "/guide",
      label: "使い方",
      icon: <BookOpen size={16} />,
      active: pathname === "/guide",
    },
    {
      href: "/documents",
      label: "ドキュメント",
      icon: <FileArchive size={16} />,
      active: pathname === "/documents",
    },
  ];

  return (
    <nav className="hidden md:flex items-center ml-6 space-x-6">
      {navItems.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={cn(
            "flex items-center text-sm font-medium transition-colors hover:text-blue-600 gap-1.5",
            item.active ? "text-blue-600" : "text-gray-600"
          )}
        >
          {item.icon}
          {item.label}
        </Link>
      ))}
    </nav>
  );
}