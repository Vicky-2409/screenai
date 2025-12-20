import { api, tokenStore } from "@/lib/api";
import type { BulkProgress, Resume } from "@/types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export interface UploadResponse {
  job_id: number;
  uploaded: Resume[];
  task_ids: string[];
  message: string;
}

export async function uploadResumes(
  jobId: number,
  files: File[],
  onProgress?: (percent: number) => void,
): Promise<UploadResponse> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  const { data } = await api.post<UploadResponse>(`/jobs/${jobId}/upload`, form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    },
  });
  return data;
}

export async function listResumes(jobId: number): Promise<Resume[]> {
  const { data } = await api.get<Resume[]>(`/jobs/${jobId}/resumes`);
  return data;
}

export async function getProgress(jobId: number): Promise<BulkProgress> {
  const { data } = await api.get<BulkProgress>(`/jobs/${jobId}/progress`);
  return data;
}

export async function deleteResume(resumeId: number): Promise<void> {
  await api.delete(`/resumes/${resumeId}`);
}

/** Fetch the original resume file as an object URL (with auth header). */
export async function fetchResumeBlobUrl(
  resumeId: number,
): Promise<{ url: string; contentType: string }> {
  const res = await fetch(`${API_BASE}/resumes/${resumeId}/file`, {
    headers: { Authorization: `Bearer ${tokenStore.access ?? ""}` },
  });
  if (!res.ok) throw new Error("Failed to load resume file");
  const contentType = res.headers.get("Content-Type") ?? "application/octet-stream";
  const blob = await res.blob();
  return { url: URL.createObjectURL(blob), contentType };
}
