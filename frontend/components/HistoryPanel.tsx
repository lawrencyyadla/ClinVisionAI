"use client";

import { Clock3 } from "lucide-react";
import type { ScanHistoryItem } from "@/lib/types";

export function HistoryPanel({ scans, onSelect }: { scans: ScanHistoryItem[]; onSelect: (scanId: string) => void }) {
  return (
    <section className="rounded-lg border border-neutral-200 bg-white p-5">
      <div className="flex items-center gap-2">
        <Clock3 className="h-5 w-5 text-neutral-700" aria-hidden />
        <h2 className="text-base font-semibold text-neutral-950">Inference History</h2>
      </div>
      <div className="mt-4 space-y-2">
        {scans.length === 0 ? (
          <p className="text-sm text-neutral-600">No scans processed yet.</p>
        ) : (
          scans.map((scan) => (
            <button
              key={scan.scan_id}
              type="button"
              onClick={() => onSelect(scan.scan_id)}
              className="focus-ring w-full rounded-lg border border-neutral-200 p-3 text-left transition hover:border-clinical"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="truncate text-sm font-medium text-neutral-900">{scan.prediction || scan.status}</p>
                <span className="shrink-0 rounded-md bg-neutral-100 px-2 py-1 text-xs text-neutral-600">{scan.file_type.toUpperCase()}</span>
              </div>
              <p className="mt-1 text-xs text-neutral-500">
                {scan.confidence == null ? "Confidence pending" : `${Math.round(scan.confidence * 100)}% confidence`} ·{" "}
                {new Date(scan.created_at).toLocaleString()}
              </p>
            </button>
          ))
        )}
      </div>
    </section>
  );
}

