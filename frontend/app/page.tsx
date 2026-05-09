"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { AlertTriangle, FileUp, RefreshCw, Server } from "lucide-react";
import { getScanResult, getScanStatus, listScans, uploadScan } from "@/lib/api";
import type { ScanHistoryItem, ScanResult, ScanStatus, UploadResponse } from "@/lib/types";
import { PipelineTimeline } from "@/components/PipelineTimeline";
import { ResultPanel } from "@/components/ResultPanel";
import { HistoryPanel } from "@/components/HistoryPanel";

const POLL_INTERVAL_MS = 1500;
const POLL_TIMEOUT_MS = Number(process.env.NEXT_PUBLIC_POLL_TIMEOUT_MS || 180000);

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [uploadResponse, setUploadResponse] = useState<UploadResponse | null>(null);
  const [status, setStatus] = useState<ScanStatus | null>(null);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [history, setHistory] = useState<ScanHistoryItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setUploading] = useState(false);
  const pollStartedAt = useRef<number | null>(null);

  async function refreshHistory() {
    try {
      setHistory(await listScans());
    } catch {
      // History is secondary to the active inference flow.
    }
  }

  useEffect(() => {
    refreshHistory();
  }, []);

  useEffect(() => {
    if (!uploadResponse || status?.status === "completed" || status?.status === "failed") {
      return;
    }

    pollStartedAt.current = pollStartedAt.current ?? Date.now();
    const interval = window.setInterval(async () => {
      if (pollStartedAt.current && Date.now() - pollStartedAt.current > POLL_TIMEOUT_MS) {
        window.clearInterval(interval);
        setError("Polling timed out. The task may still be running; refresh history in a moment.");
        return;
      }

      try {
        const nextStatus = await getScanStatus(uploadResponse.task_id);
        setStatus(nextStatus);
        if (nextStatus.status === "completed" || nextStatus.status === "failed") {
          window.clearInterval(interval);
          const nextResult = await getScanResult(nextStatus.scan_id);
          setResult(nextResult);
          await refreshHistory();
        }
      } catch (err) {
        window.clearInterval(interval);
        setError(err instanceof Error ? err.message : "Unable to poll task status.");
      }
    }, POLL_INTERVAL_MS);

    return () => window.clearInterval(interval);
  }, [uploadResponse, status?.status]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      setError("Select a JPG, PNG, or DICOM file first.");
      return;
    }

    setUploading(true);
    setError(null);
    setStatus(null);
    setResult(null);
    pollStartedAt.current = Date.now();

    try {
      const response = await uploadScan(file);
      setUploadResponse(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  async function loadResult(scanId: string) {
    setError(null);
    try {
      setResult(await getScanResult(scanId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load result.");
    }
  }

  const visibleStatus =
    status ||
    (uploadResponse
      ? {
          scan_id: uploadResponse.scan_id,
          task_id: uploadResponse.task_id,
          status: uploadResponse.status,
          current_stage: uploadResponse.current_stage,
          stages: [
            { name: "Upload received", state: "completed" as const, timestamp: null },
            { name: "Validating file", state: "pending" as const, timestamp: null },
            { name: "Sanitizing metadata", state: "pending" as const, timestamp: null },
            { name: "Converting DICOM preview", state: "pending" as const, timestamp: null },
            { name: "Running DenseNet121 inference", state: "pending" as const, timestamp: null },
            { name: "Generating Grad-CAM heatmap", state: "pending" as const, timestamp: null },
            { name: "Generating AI findings", state: "pending" as const, timestamp: null },
            { name: "Completed", state: "pending" as const, timestamp: null }
          ],
          error_message: null,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      : null);

  return (
    <main className="min-h-screen bg-[#f7f7f4]">
      <header className="border-b border-neutral-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 py-5">
          <div>
            <h1 className="text-2xl font-semibold text-neutral-950">ClinVision AI</h1>
            <p className="mt-1 text-sm text-neutral-600">Asynchronous chest X-ray inference with explainability and observability.</p>
          </div>
          <div className="flex items-center gap-2 rounded-lg border border-neutral-200 px-3 py-2 text-sm text-neutral-700">
            <Server className="h-4 w-4 text-clinical" aria-hidden />
            Local MVP
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-5 px-5 py-6 lg:grid-cols-[390px_minmax(0,1fr)]">
        <div className="space-y-5">
          <section className="rounded-lg border border-neutral-200 bg-white p-5">
            <div className="flex items-center gap-2">
              <FileUp className="h-5 w-5 text-clinical" aria-hidden />
              <h2 className="text-base font-semibold text-neutral-950">Upload Scan</h2>
            </div>
            <form className="mt-4 space-y-4" onSubmit={onSubmit}>
              <label className="block rounded-lg border border-dashed border-neutral-300 bg-neutral-50 p-4">
                <span className="text-sm font-medium text-neutral-800">Chest X-ray file</span>
                <input
                  className="mt-3 block w-full text-sm text-neutral-700 file:mr-3 file:rounded-md file:border-0 file:bg-clinical file:px-3 file:py-2 file:text-sm file:font-semibold file:text-white"
                  type="file"
                  accept=".jpg,.jpeg,.png,.dcm,image/jpeg,image/png"
                  onChange={(event) => setFile(event.target.files?.[0] || null)}
                />
              </label>
              <button
                type="submit"
                disabled={isUploading}
                className="focus-ring inline-flex w-full items-center justify-center gap-2 rounded-lg bg-clinical px-4 py-3 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-neutral-400"
              >
                {isUploading ? <RefreshCw className="h-4 w-4 animate-spin" aria-hidden /> : <FileUp className="h-4 w-4" aria-hidden />}
                {isUploading ? "Uploading" : "Start Inference"}
              </button>
            </form>
            {error ? (
              <div className="mt-4 flex gap-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
                <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
                <p>{error}</p>
              </div>
            ) : null}
          </section>

          <section className="rounded-lg border border-neutral-200 bg-white p-5">
            <h2 className="text-base font-semibold text-neutral-950">Pipeline Status</h2>
            <p className="mt-1 text-sm text-neutral-600">{visibleStatus ? visibleStatus.current_stage : "Waiting for upload"}</p>
            <div className="mt-4">
              {visibleStatus ? <PipelineTimeline stages={visibleStatus.stages} /> : <p className="text-sm text-neutral-500">No active task.</p>}
            </div>
          </section>
        </div>

        <div className="space-y-5">
          <ResultPanel result={result} />
          <HistoryPanel scans={history} onSelect={loadResult} />
        </div>
      </div>
    </main>
  );
}

