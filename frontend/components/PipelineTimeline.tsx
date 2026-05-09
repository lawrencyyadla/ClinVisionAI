"use client";

import { Check, Circle, LoaderCircle, X } from "lucide-react";
import type { PipelineStage } from "@/lib/types";

const stateStyles = {
  pending: "border-neutral-300 bg-white text-neutral-400",
  active: "border-clinical bg-white text-clinical",
  completed: "border-clinical bg-clinical text-white",
  failed: "border-red-600 bg-red-600 text-white"
};

export function PipelineTimeline({ stages }: { stages: PipelineStage[] }) {
  return (
    <ol className="space-y-3">
      {stages.map((stage) => (
        <li key={stage.name} className="flex items-center gap-3">
          <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border ${stateStyles[stage.state]}`}>
            {stage.state === "completed" && <Check className="h-4 w-4" aria-hidden />}
            {stage.state === "active" && <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden />}
            {stage.state === "failed" && <X className="h-4 w-4" aria-hidden />}
            {stage.state === "pending" && <Circle className="h-3 w-3" aria-hidden />}
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-neutral-900">{stage.name}</p>
            <p className="text-xs capitalize text-neutral-500">{stage.state}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}

