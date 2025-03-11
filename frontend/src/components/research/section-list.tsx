"use client";

import { Badge } from "@/components/ui/badge";
import { SectionModel } from "@/types/api";

interface SectionListProps {
  sections: SectionModel[];
  completedSections?: string[];
}

export function SectionList({ sections, completedSections = [] }: SectionListProps) {
  return (
    <div className="space-y-4">
      {sections.map((section, index) => {
        // セクションの状態を判定
        let status = "waiting";
        if (completedSections.includes(section.name)) {
          status = "completed";
        } else if (
          index > 0 && 
          completedSections.includes(sections[index - 1].name) && 
          !completedSections.includes(section.name)
        ) {
          status = "in_progress";
        }

        return (
          <div 
            key={index} 
            className="flex items-center justify-between p-4 bg-gray-50 rounded-md border"
          >
            <div className="flex-1">
              <h3 className="font-medium">{section.name}</h3>
              <p className="text-sm text-gray-600">{section.description}</p>
            </div>
            <Badge 
              variant={status === "completed" ? "default" : "outline"}
              className={`ml-4 flex-shrink-0 ${
                status === "completed" 
                  ? "bg-green-500" 
                  : status === "in_progress" 
                    ? "border-blue-500 text-blue-600" 
                    : "border-gray-300 text-gray-500"
              }`}
            >
              {status === "completed" ? "完了" : status === "in_progress" ? "進行中" : "待機中"}
            </Badge>
          </div>
        );
      })}
    </div>
  );
}