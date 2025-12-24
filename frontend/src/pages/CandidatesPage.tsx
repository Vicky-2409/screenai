import { useMutation, useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, RefreshCw, Search, Sparkles, Users } from "lucide-react";
import { useState } from "react";
import toast from "react-hot-toast";
import { useNavigate, useParams } from "react-router-dom";

import { HtmlContent } from "@/components/RichTextEditor";
import { EmptyState, PageHeader, ScoreBadge, Skeleton, StatusBadge } from "@/components/ui";
import { apiErrorMessage } from "@/lib/api";
import { getJob } from "@/services/jobs";
import { listCandidates, rescreenJob, semanticSearch } from "@/services/candidates";
import type { CandidateStatus, RankedCandidate } from "@/types";

const STATUS_OPTIONS: (CandidateStatus | "all")[] = [
  "all",
  "new",
  "shortlisted",
  "interviewing",
  "hired",
  "rejected",
];

export function CandidatesPage() {
  const { jobId } = useParams();
  const id = Number(jobId);
  const navigate = useNavigate();

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<CandidateStatus | "all">("all");
  const [sortBy, setSortBy] = useState("overall_score");
  const [page, setPage] = useState(1);
  const [semanticQuery, setSemanticQuery] = useState("");
  const [semanticResults, setSemanticResults] = useState<RankedCandidate[] | null>(null);
  const pageSize = 10;

  const { data: job } = useQuery({ queryKey: ["job", jobId], queryFn: () => getJob(id) });

  const { data, isLoading } = useQuery({
    queryKey: ["candidates", id, search, status, sortBy, page],
    queryFn: () =>
      listCandidates(id, {
        search: search || undefined,
        status: status === "all" ? undefined : status,
        sort_by: sortBy,
        page,
        page_size: pageSize,
      }),
  });

  const rescreen = useMutation({
    mutationFn: () => rescreenJob(id),
    onSuccess: () => toast.success("Re-screening started"),
    onError: (err) => toast.error(apiErrorMessage(err)),
  });

  const semanticMutation = useMutation({
    mutationFn: () => semanticSearch(semanticQuery, id, 20),
    onSuccess: (res) => {
      setSemanticResults(res);
      toast.success(`${res.length} semantic matches`);
    },
    onError: (err) => toast.error(apiErrorMessage(err)),
  });

  const rows = semanticResults ?? data?.items ?? [];
  const totalPages = data ? Math.max(1, Math.ceil(data.total / pageSize)) : 1;

  return (
    <div>
      <PageHeader
        title={job ? `Candidates - ${job.title}` : "Candidates"}
        subtitle="AI-ranked candidates for this role"
        action={
          <div className="flex gap-2">
            <button className="btn-secondary" onClick={() => navigate(`/jobs/${id}/upload`)}>
              Upload more
            </button>
            <button
              className="btn-primary"
              onClick={() => rescreen.mutate()}
              disabled={rescreen.isPending}
            >
              <RefreshCw size={15} className={rescreen.isPending ? "animate-spin" : ""} /> Re-screen
            </button>
          </div>
        }
      />

      {/* Job description (rich text) */}
      {job && (job.description || job.responsibilities || job.qualifications) && (
        <details className="card mb-4 group">
          <summary className="cursor-pointer select-none font-semibold">Job description</summary>
          <div className="mt-3 space-y-3">
            {job.description && <HtmlContent html={job.description} />}
            {job.responsibilities && (
              <div>
                <p className="mb-1 text-xs font-semibold uppercase text-slate-500">Responsibilities</p>
                <HtmlContent html={job.responsibilities} />
              </div>
            )}
            {job.qualifications && (
              <div>
                <p className="mb-1 text-xs font-semibold uppercase text-slate-500">Qualifications</p>
                <HtmlContent html={job.qualifications} />
              </div>
            )}
          </div>
        </details>
      )}

      {/* Semantic search */}
      <div className="card mb-4">
        <label className="label flex items-center gap-2">
          <Sparkles size={15} className="text-brand-500" /> Semantic Search
        </label>
        <div className="flex gap-2">
          <input
            className="input"
            placeholder='e.g. "Python developer with FastAPI and AWS"'
            value={semanticQuery}
            onChange={(e) => setSemanticQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && semanticQuery && semanticMutation.mutate()}
          />
          <button
            className="btn-primary"
            onClick={() => semanticMutation.mutate()}
            disabled={!semanticQuery || semanticMutation.isPending}
          >
            Search
          </button>
          {semanticResults && (
            <button className="btn-ghost" onClick={() => setSemanticResults(null)}>
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      {!semanticResults && (
        <div className="card mb-4 flex flex-wrap items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
            <input
              className="input pl-9"
              placeholder="Search by name, email, role"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
            />
          </div>
          <select
            className="input w-auto"
            value={status}
            onChange={(e) => {
              setStatus(e.target.value as CandidateStatus | "all");
              setPage(1);
            }}
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s === "all" ? "All statuses" : s}
              </option>
            ))}
          </select>
          <select className="input w-auto" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="overall_score">Sort: Score</option>
            <option value="experience">Sort: Experience</option>
            <option value="name">Sort: Name</option>
          </select>
        </div>
      )}

      {isLoading && (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-14 rounded-xl" />
          ))}
        </div>
      )}

      {!isLoading && rows.length === 0 && (
        <EmptyState
          icon={Users}
          title="No candidates yet"
          description="Upload resumes to see AI-ranked candidates here."
          action={
            <button className="btn-primary" onClick={() => navigate(`/jobs/${id}/upload`)}>
              Upload resumes
            </button>
          }
        />
      )}

      {rows.length > 0 && (
        <div className="card overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase text-slate-500 dark:border-slate-700">
              <tr>
                <th className="px-4 py-3">Rank</th>
                <th className="px-4 py-3">Candidate</th>
                <th className="px-4 py-3">Score</th>
                <th className="px-4 py-3">Exp</th>
                <th className="px-4 py-3">Top Skills</th>
                <th className="px-4 py-3">Recommendation</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={row.candidate.id}
                  onClick={() => navigate(`/candidates/${row.candidate.id}?job_id=${id}`)}
                  className="cursor-pointer border-b border-slate-100 transition hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                >
                  <td className="px-4 py-3 font-semibold text-slate-400">#{row.rank}</td>
                  <td className="px-4 py-3">
                    <p className="font-medium">{row.candidate.name || "Unknown"}</p>
                    <p className="text-xs text-slate-400">{row.candidate.email || "-"}</p>
                  </td>
                  <td className="px-4 py-3">
                    <ScoreBadge score={row.score.overall_score} />
                  </td>
                  <td className="px-4 py-3">{row.candidate.total_experience_years.toFixed(0)}y</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {row.candidate.skills.slice(0, 3).map((s) => (
                        <span key={s} className="badge bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                          {s}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="max-w-[200px] truncate px-4 py-3 text-xs text-slate-500">
                    {row.score.recommendation || "-"}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={row.score.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!semanticResults && data && data.total > pageSize && (
        <div className="mt-4 flex items-center justify-between text-sm">
          <span className="text-slate-500">
            Page {page} of {totalPages} - {data.total} candidates
          </span>
          <div className="flex gap-2">
            <button
              className="btn-secondary"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              <ChevronLeft size={16} /> Prev
            </button>
            <button
              className="btn-secondary"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
