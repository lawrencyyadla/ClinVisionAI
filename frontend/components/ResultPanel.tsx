"use client";

import { Activity, AlertTriangle, FileText, Timer } from "lucide-react";
import { assetUrl } from "@/lib/api";
import type { ScanResult } from "@/lib/types";

function confidenceClass(status: string | null) {
  if (status === "High Confidence") {
    return "border-clinical bg-teal-50 text-clinical";
  }
  if (status === "Moderate Confidence") {
    return "border-signal bg-amber-50 text-signal";
  }
  return "border-red-600 bg-red-50 text-red-700";
}

export function ResultPanel({ result }: { result: ScanResult | null }) {
  if (!result) {
    return (
      <section className="rounded-lg border border-neutral-200 bg-white p-5">
        <h2 className="text-base font-semibold text-neutral-950">Inference Result</h2>
        <p className="mt-2 text-sm text-neutral-600">Upload a chest X-ray to start an asynchronous inference task.</p>
      </section>
    );
  }

  const overlay = assetUrl(result.overlay_url);
  const converted = assetUrl(result.converted_image_url);

  return (
    <section className="rounded-lg border border-neutral-200 bg-white p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-neutral-950">Inference Result</h2>
          <p className="mt-1 text-xs text-neutral-500">Scan {result.scan_id.slice(0, 8)}</p>
        </div>
        <span className={`rounded-md border px-3 py-1 text-xs font-semibold ${confidenceClass(result.confidence_status)}`}>
          {result.confidence_status || result.status}
        </span>
      </div>

      {result.status === "failed" ? (
        <div className="mt-5 flex gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <p>{result.error_message || "Inference failed."}</p>
        </div>
      ) : (
        <>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg border border-neutral-200 p-4">
              <Activity className="h-5 w-5 text-clinical" aria-hidden />
              <p className="mt-3 text-xs text-neutral-500">Prediction</p>
              <p className="mt-1 text-lg font-semibold text-neutral-950">{result.prediction || "Pending"}</p>
            </div>
            <div className="rounded-lg border border-neutral-200 p-4">
              <FileText className="h-5 w-5 text-signal" aria-hidden />
              <p className="mt-3 text-xs text-neutral-500">Confidence</p>
              <p className="mt-1 text-lg font-semibold text-neutral-950">
                {result.confidence == null ? "Pending" : `${Math.round(result.confidence * 100)}%`}
              </p>
            </div>
            <div className="rounded-lg border border-neutral-200 p-4">
              <Timer className="h-5 w-5 text-neutral-700" aria-hidden />
              <p className="mt-3 text-xs text-neutral-500">Latency</p>
              <p className="mt-1 text-lg font-semibold text-neutral-950">
                {result.latency_ms == null ? "Pending" : `${result.latency_ms} ms`}
              </p>
            </div>
          </div>

          <div className="mt-5 grid gap-4 lg:grid-cols-2">
            <figure className="rounded-lg border border-neutral-200 p-3">
              <figcaption className="mb-2 text-xs font-medium text-neutral-500">Converted Preview</figcaption>
              {converted ? <img className="aspect-square w-full rounded-md object-contain bg-neutral-950" src={converted} alt="Converted chest X-ray preview" /> : null}
            </figure>
            <figure className="rounded-lg border border-neutral-200 p-3">
              <figcaption className="mb-2 text-xs font-medium text-neutral-500">Grad-CAM Overlay</figcaption>
              {overlay ? <img className="aspect-square w-full rounded-md object-contain bg-neutral-950" src={overlay} alt="Grad-CAM heatmap overlay" /> : null}
            </figure>
          </div>

          <div className="mt-5 rounded-lg border border-neutral-200 p-4">
            <p className="text-xs font-medium uppercase text-neutral-500">Educational Findings</p>
            <p className="mt-2 text-sm leading-6 text-neutral-800">{result.report_text}</p>
          </div>

          <dl className="mt-5 grid gap-2 text-xs text-neutral-600 sm:grid-cols-3">
            <div>
              <dt className="font-medium text-neutral-500">Model</dt>
              <dd>{result.model_name || "DenseNet121"}</dd>
            </div>
            <div>
              <dt className="font-medium text-neutral-500">Version</dt>
              <dd>{result.model_version || "Unavailable"}</dd>
            </div>
            <div>
              <dt className="font-medium text-neutral-500">Hash</dt>
              <dd>{result.model_hash || "Unavailable"}</dd>
            </div>
          </dl>
        </>
      )}
    </section>
  );
}

