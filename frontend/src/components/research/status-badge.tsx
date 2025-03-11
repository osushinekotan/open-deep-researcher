"use client";

import { Badge } from "@/components/ui/badge";
import { getStatusInfo } from "@/lib/utils";

interface StatusBadgeProps {
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const { label, color } = getStatusInfo(status);
  
  // 直接カスタムスタイルを適用
  const badgeStyles = {
    completed: "bg-green-500 hover:bg-green-600 text-white",
    waiting_for_feedback: "bg-yellow-500 hover:bg-yellow-600 text-white",
    researching_sections: "bg-blue-500 hover:bg-blue-600 text-white",
    processing_sections: "bg-blue-500 hover:bg-blue-600 text-white",
    planning: "bg-purple-500 hover:bg-purple-600 text-white",
    initializing: "bg-gray-500 hover:bg-gray-600 text-white",
    error: "bg-red-500 hover:bg-red-600 text-white",
    default: "bg-gray-500 hover:bg-gray-600 text-white"
  };
  
  const badgeStyle = badgeStyles[status as keyof typeof badgeStyles] || badgeStyles.default;
  
  return (
    <Badge className={`font-medium ${badgeStyle}`}>
      {label}
    </Badge>
  );
}