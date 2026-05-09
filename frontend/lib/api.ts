import type { ScanHistoryItem, ScanResult, ScanStatus, UploadResponse } from "./types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // keep response status text
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export function assetUrl(path: string | null): string | null {
  if (!path) {
    return null;
  }
  if (path.startsWith("http")) {
    return path;
  }
  return `${API_BASE_URL}${path}`;
}

export function uploadScan(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("upload", file);
  return request<UploadResponse>("/api/scans", {
    method: "POST",
    body: form
  });
}

export function getScanStatus(taskId: string): Promise<ScanStatus> {
  return request<ScanStatus>(`/api/scans/${taskId}/status`, { cache: "no-store" });
}

export function getScanResult(scanId: string): Promise<ScanResult> {
  return request<ScanResult>(`/api/scans/result/${scanId}`, { cache: "no-store" });
}

export function listScans(): Promise<ScanHistoryItem[]> {
  return request<ScanHistoryItem[]>("/api/scans", { cache: "no-store" });
}

