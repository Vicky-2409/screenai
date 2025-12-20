import { api } from "@/lib/api";
import type {
  CandidateDetail,
  CandidateListResponse,
  CandidateStatus,
  RankedCandidate,
  Score,
  SkillGap,
} from "@/types";

export interface CandidateQuery {
  search?: string;
  status?: CandidateStatus;
  min_score?: number;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

export async function listCandidates(
  jobId: number,
  query: CandidateQuery = {},
): Promise<CandidateListResponse> {
  const { data } = await api.get<CandidateListResponse>(`/jobs/${jobId}/candidates`, {
    params: query,
  });
  return data;
}

export async function getCandidate(id: number, jobId?: number): Promise<CandidateDetail> {
  const { data } = await api.get<CandidateDetail>(`/candidates/${id}`, {
    params: { job_id: jobId },
  });
  return data;
}

export async function getSkillGap(id: number, jobId?: number): Promise<SkillGap> {
  const { data } = await api.get<SkillGap>(`/candidates/${id}/skill-gap`, {
    params: { job_id: jobId },
  });
  return data;
}

export async function updateStatus(
  id: number,
  status: CandidateStatus,
  jobId?: number,
): Promise<Score> {
  const { data } = await api.patch<Score>(
    `/candidates/${id}/status`,
    { status },
    { params: { job_id: jobId } },
  );
  return data;
}

export async function updateNotes(id: number, notes: string): Promise<void> {
  await api.patch(`/candidates/${id}/notes`, { notes });
}

export async function semanticSearch(
  query: string,
  jobId?: number,
  limit = 20,
): Promise<RankedCandidate[]> {
  const { data } = await api.post<RankedCandidate[]>("/search", {
    query,
    job_id: jobId,
    limit,
  });
  return data;
}

export async function rescreenJob(jobId: number): Promise<{ task_id: string }> {
  const { data } = await api.post("/screen", { job_id: jobId });
  return data;
}

export async function reanalyzeCandidate(candidateId: number, jobId?: number): Promise<Score> {
  const { data } = await api.post<Score>("/analyze", {
    candidate_id: candidateId,
    job_id: jobId,
  });
  return data;
}
