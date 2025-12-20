import { api } from "@/lib/api";
import type { Job, JobInput } from "@/types";

export async function listJobs(): Promise<Job[]> {
  const { data } = await api.get<Job[]>("/jobs");
  return data;
}

export async function getJob(id: number): Promise<Job> {
  const { data } = await api.get<Job>(`/jobs/${id}`);
  return data;
}

export async function createJob(payload: JobInput): Promise<Job> {
  const { data } = await api.post<Job>("/jobs", payload);
  return data;
}

export async function updateJob(id: number, payload: JobInput): Promise<Job> {
  const { data } = await api.put<Job>(`/jobs/${id}`, payload);
  return data;
}

export async function deleteJob(id: number): Promise<void> {
  await api.delete(`/jobs/${id}`);
}
