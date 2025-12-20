import { api } from "@/lib/api";
import type { User } from "@/types";

export interface AdminStats {
  total_users: number;
  total_jobs: number;
  total_resumes: number;
  total_candidates: number;
}

export interface ActivityLogEntry {
  id: number;
  user_id: number | null;
  action: string;
  entity_type: string | null;
  entity_id: number | null;
  message: string | null;
  created_at: string;
}

export async function getAdminStats(): Promise<AdminStats> {
  const { data } = await api.get<AdminStats>("/admin/stats");
  return data;
}

export async function listUsers(): Promise<User[]> {
  const { data } = await api.get<User[]>("/admin/users");
  return data;
}

export async function toggleUserActive(userId: number): Promise<User> {
  const { data } = await api.post<User>(`/admin/users/${userId}/toggle-active`);
  return data;
}

export async function listLogs(): Promise<ActivityLogEntry[]> {
  const { data } = await api.get<ActivityLogEntry[]>("/admin/logs");
  return data;
}

export interface StorageBreakdown {
  label: string;
  files: number;
  bytes: number;
}

export interface StorageStats {
  total_bytes: number;
  total_files: number;
  breakdown: StorageBreakdown[];
}

export async function getStorageStats(): Promise<StorageStats> {
  const { data } = await api.get<StorageStats>("/admin/storage");
  return data;
}
