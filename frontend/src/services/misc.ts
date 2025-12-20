import { api, tokenStore } from "@/lib/api";
import type { DashboardAnalytics, Notification } from "@/types";

export async function getDashboard(): Promise<DashboardAnalytics> {
  const { data } = await api.get<DashboardAnalytics>("/analytics/dashboard");
  return data;
}

export async function listNotifications(unreadOnly = false): Promise<Notification[]> {
  const { data } = await api.get<Notification[]>("/notifications", {
    params: { unread_only: unreadOnly },
  });
  return data;
}

export async function markNotificationRead(id: number): Promise<void> {
  await api.post(`/notifications/${id}/read`);
}

export async function markAllNotificationsRead(): Promise<void> {
  await api.post("/notifications/read-all");
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

/** Trigger a browser download for an authenticated report endpoint. */
export async function downloadReport(jobId: number, kind: "pdf" | "csv"): Promise<void> {
  const res = await fetch(`${API_BASE}/reports/${jobId}/${kind}`, {
    headers: { Authorization: `Bearer ${tokenStore.access ?? ""}` },
  });
  if (!res.ok) throw new Error("Failed to generate report");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = kind === "pdf" ? `job_${jobId}_report.pdf` : `job_${jobId}_candidates.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
