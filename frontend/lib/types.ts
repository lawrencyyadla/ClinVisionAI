export type PipelineStage = {
  name: string;
  state: "pending" | "active" | "completed" | "failed";
  timestamp: string | null;
};

export type UploadResponse = {
  scan_id: string;
  task_id: string;
  status: string;
  current_stage: string;
};

export type ScanStatus = {
  scan_id: string;
  task_id: string;
  status: string;
  current_stage: string;
  stages: PipelineStage[];
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type ScanResult = {
  scan_id: string;
  task_id: string;
  status: string;
  file_type: string;
  converted_image_url: string | null;
  heatmap_url: string | null;
  overlay_url: string | null;
  prediction: string | null;
  confidence: number | null;
  confidence_status: string | null;
  report_text: string | null;
  model_name: string | null;
  model_version: string | null;
  model_hash: string | null;
  latency_ms: number | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type ScanHistoryItem = {
  scan_id: string;
  task_id: string;
  status: string;
  file_type: string;
  prediction: string | null;
  confidence: number | null;
  confidence_status: string | null;
  latency_ms: number | null;
  created_at: string;
  updated_at: string;
};

