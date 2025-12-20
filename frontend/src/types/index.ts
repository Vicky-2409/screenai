export type UserRole = "recruiter" | "admin";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export type EmploymentType =
  | "full_time"
  | "part_time"
  | "contract"
  | "internship"
  | "temporary";

export type JobStatus = "open" | "closed" | "draft";

export interface Job {
  id: number;
  owner_id: number;
  title: string;
  department?: string | null;
  location?: string | null;
  experience?: string | null;
  min_experience_years: number;
  salary?: string | null;
  employment_type: EmploymentType;
  status: JobStatus;
  description?: string | null;
  responsibilities?: string | null;
  qualifications?: string | null;
  skills: string[];
  created_at: string;
  updated_at: string;
  resume_count?: number;
  scored_count?: number;
  average_score?: number;
}

export interface JobInput {
  title: string;
  department?: string;
  location?: string;
  experience?: string;
  min_experience_years?: number;
  salary?: string;
  employment_type?: EmploymentType;
  description?: string;
  responsibilities?: string;
  qualifications?: string;
  skills?: string[];
  status?: JobStatus;
}

export type ResumeStatus =
  | "uploaded"
  | "parsing"
  | "parsed"
  | "scoring"
  | "scored"
  | "failed";

export interface Resume {
  id: number;
  job_id: number;
  original_filename: string;
  content_type?: string | null;
  file_size: number;
  status: ResumeStatus;
  error?: string | null;
  created_at: string;
}

export interface BulkProgress {
  job_id: number;
  total: number;
  parsed: number;
  scored: number;
  failed: number;
  pending: number;
}

export type CandidateStatus =
  | "new"
  | "shortlisted"
  | "rejected"
  | "interviewing"
  | "hired";

export interface CandidateBase {
  id: number;
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  designation?: string | null;
  total_experience_years: number;
  skills: string[];
}

export interface Score {
  overall_score: number;
  semantic_score: number;
  skill_score: number;
  experience_score: number;
  education_score: number;
  keyword_score: number;
  matching_skills: string[];
  missing_skills: string[];
  additional_skills: string[];
  summary?: string | null;
  strengths: string[];
  weaknesses: string[];
  recommendation?: string | null;
  culture_fit?: string | null;
  interview_questions: string[];
  score_breakdown: Record<string, unknown>;
  status: CandidateStatus;
}

export interface RankedCandidate {
  rank: number;
  candidate: CandidateBase;
  score: Score;
}

export interface CandidateDetail extends CandidateBase {
  education: Record<string, unknown>[];
  experience: Record<string, unknown>[];
  certifications: string[];
  projects: Record<string, unknown>[];
  companies: string[];
  notes?: string | null;
  resume_id: number;
  created_at: string;
  score?: Score | null;
}

export interface CandidateListResponse {
  total: number;
  page: number;
  page_size: number;
  items: RankedCandidate[];
}

export interface SkillGap {
  matched: string[];
  missing: string[];
  additional: string[];
  job_skills: string[];
  candidate_skills: string[];
}

export interface StatPoint {
  label: string;
  value: number;
}

export interface DashboardStats {
  total_jobs: number;
  total_resumes: number;
  candidates_screened: number;
  average_match_score: number;
  processing_queue: number;
}

export interface DashboardAnalytics {
  stats: DashboardStats;
  skill_distribution: StatPoint[];
  score_distribution: StatPoint[];
  top_skills: StatPoint[];
  missing_skills: StatPoint[];
  hiring_funnel: StatPoint[];
  resume_sources: StatPoint[];
  job_performance: StatPoint[];
  recent_activity: Record<string, unknown>[];
  time_saved_hours: number;
}

export interface Notification {
  id: number;
  title: string;
  message?: string | null;
  level: "info" | "success" | "warning" | "error";
  read: boolean;
  created_at: string;
}
