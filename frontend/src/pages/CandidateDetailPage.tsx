import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Award,
  Briefcase,
  GraduationCap,
  Lightbulb,
  Loader2,
  Mail,
  MapPin,
  Phone,
  Sparkles,
} from "lucide-react";
import { useState } from "react";
import toast from "react-hot-toast";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";

import { ResumePreview } from "@/components/ResumePreview";
import { PageHeader, ProgressBar, ScoreBadge, SkillChip, StatusBadge } from "@/components/ui";
import { apiErrorMessage } from "@/lib/api";
import {
  getCandidate,
  getSkillGap,
  reanalyzeCandidate,
  updateNotes,
  updateStatus,
} from "@/services/candidates";
import type { CandidateStatus } from "@/types";

const STATUSES: CandidateStatus[] = ["new", "shortlisted", "interviewing", "hired", "rejected"];

export function CandidateDetailPage() {
  const { candidateId } = useParams();
  const id = Number(candidateId);
  const [searchParams] = useSearchParams();
  const jobId = searchParams.get("job_id") ? Number(searchParams.get("job_id")) : undefined;
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [notes, setNotes] = useState("");

  const { data: candidate, isLoading } = useQuery({
    queryKey: ["candidate", id, jobId],
    queryFn: () => getCandidate(id, jobId),
  });

  const { data: skillGap } = useQuery({
    queryKey: ["skillgap", id, jobId],
    queryFn: () => getSkillGap(id, jobId),
  });

  const statusMutation = useMutation({
    mutationFn: (status: CandidateStatus) => updateStatus(id, status, jobId),
    onSuccess: () => {
      toast.success("Status updated");
      void queryClient.invalidateQueries({ queryKey: ["candidate", id, jobId] });
    },
    onError: (err) => toast.error(apiErrorMessage(err)),
  });

  const notesMutation = useMutation({
    mutationFn: () => updateNotes(id, notes),
    onSuccess: () => toast.success("Notes saved"),
  });

  const reanalyze = useMutation({
    mutationFn: () => reanalyzeCandidate(id, jobId),
    onSuccess: () => {
      toast.success("AI analysis refreshed");
      void queryClient.invalidateQueries({ queryKey: ["candidate", id, jobId] });
    },
    onError: (err) => toast.error(apiErrorMessage(err)),
  });

  if (isLoading || !candidate) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="animate-spin text-brand-500" size={28} />
      </div>
    );
  }

  const score = candidate.score;
  const radarData = score
    ? [
        { metric: "Semantic", value: score.semantic_score },
        { metric: "Skills", value: score.skill_score },
        { metric: "Experience", value: score.experience_score },
        { metric: "Education", value: score.education_score },
        { metric: "Keywords", value: score.keyword_score },
      ]
    : [];

  return (
    <div>
      <button className="btn-ghost mb-2" onClick={() => navigate(-1)}>
        <ArrowLeft size={16} /> Back
      </button>

      <PageHeader
        title={candidate.name || "Unknown Candidate"}
        subtitle={candidate.designation || "Candidate profile"}
        action={
          <div className="flex items-center gap-2">
            <select
              className="input w-auto"
              value={score?.status ?? "new"}
              onChange={(e) => statusMutation.mutate(e.target.value as CandidateStatus)}
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <button className="btn-primary" onClick={() => reanalyze.mutate()} disabled={reanalyze.isPending}>
              {reanalyze.isPending ? <Loader2 className="animate-spin" size={15} /> : <Sparkles size={15} />}
              Re-analyze
            </button>
          </div>
        }
      />

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left column */}
        <div className="space-y-6">
          <div className="card">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Contact</h3>
              {score && <StatusBadge status={score.status} />}
            </div>
            <ul className="mt-3 space-y-2 text-sm text-slate-600 dark:text-slate-300">
              {candidate.email && (
                <li className="flex items-center gap-2">
                  <Mail size={14} /> {candidate.email}
                </li>
              )}
              {candidate.phone && (
                <li className="flex items-center gap-2">
                  <Phone size={14} /> {candidate.phone}
                </li>
              )}
              {candidate.location && (
                <li className="flex items-center gap-2">
                  <MapPin size={14} /> {candidate.location}
                </li>
              )}
              <li className="flex items-center gap-2">
                <Briefcase size={14} /> {candidate.total_experience_years.toFixed(0)} years experience
              </li>
            </ul>
          </div>

          {score && (
            <motion.div className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <div className="mb-3 flex items-center justify-between">
                <h3 className="font-semibold">Match Breakdown</h3>
                <ScoreBadge score={score.overall_score} />
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11 }} />
                  <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                  <Radar dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.4} />
                </RadarChart>
              </ResponsiveContainer>
              <div className="mt-2 space-y-2 text-xs">
                {radarData.map((d) => (
                  <div key={d.metric}>
                    <div className="mb-0.5 flex justify-between">
                      <span>{d.metric}</span>
                      <span className="font-semibold">{d.value.toFixed(0)}%</span>
                    </div>
                    <ProgressBar value={d.value} />
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          <div className="card">
            <h3 className="mb-2 font-semibold">Recruiter Notes</h3>
            <textarea
              className="input min-h-[100px]"
              placeholder="Add private notes..."
              defaultValue={candidate.notes ?? ""}
              onChange={(e) => setNotes(e.target.value)}
            />
            <button className="btn-secondary mt-2 w-full" onClick={() => notesMutation.mutate()}>
              Save notes
            </button>
          </div>

          <ResumePreview resumeId={candidate.resume_id} filename={candidate.name ?? undefined} />
        </div>

        {/* Right column */}
        <div className="space-y-6 lg:col-span-2">
          {score && (
            <div className="card">
              <h3 className="mb-2 flex items-center gap-2 font-semibold">
                <Sparkles size={16} className="text-brand-500" /> AI Summary
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-300">{score.summary || "No summary yet."}</p>
              {score.recommendation && (
                <div className="mt-3 rounded-xl bg-brand-50 p-3 text-sm font-medium text-brand-700 dark:bg-brand-600/10 dark:text-brand-300">
                  {score.recommendation}
                </div>
              )}
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="mb-1 text-sm font-semibold text-emerald-600">Strengths</p>
                  <ul className="list-inside list-disc space-y-1 text-sm text-slate-600 dark:text-slate-300">
                    {score.strengths.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="mb-1 text-sm font-semibold text-rose-500">Weaknesses</p>
                  <ul className="list-inside list-disc space-y-1 text-sm text-slate-600 dark:text-slate-300">
                    {score.weaknesses.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {skillGap && (
            <div className="card">
              <h3 className="mb-3 font-semibold">Skill Gap Analysis</h3>
              <div className="space-y-3">
                <div>
                  <p className="mb-1 text-xs font-semibold uppercase text-emerald-600">Matched</p>
                  <div className="flex flex-wrap gap-1">
                    {skillGap.matched.length ? (
                      skillGap.matched.map((s) => <SkillChip key={s} variant="match">{s}</SkillChip>)
                    ) : (
                      <span className="text-sm text-slate-400">None</span>
                    )}
                  </div>
                </div>
                <div>
                  <p className="mb-1 text-xs font-semibold uppercase text-rose-500">Missing</p>
                  <div className="flex flex-wrap gap-1">
                    {skillGap.missing.length ? (
                      skillGap.missing.map((s) => <SkillChip key={s} variant="missing">{s}</SkillChip>)
                    ) : (
                      <span className="text-sm text-slate-400">None</span>
                    )}
                  </div>
                </div>
                <div>
                  <p className="mb-1 text-xs font-semibold uppercase text-slate-500">Additional</p>
                  <div className="flex flex-wrap gap-1">
                    {skillGap.additional.slice(0, 15).map((s) => (
                      <SkillChip key={s}>{s}</SkillChip>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="grid gap-6 sm:grid-cols-2">
            <div className="card">
              <h3 className="mb-2 flex items-center gap-2 font-semibold">
                <Briefcase size={16} /> Experience
              </h3>
              <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-300">
                {candidate.experience.length ? (
                  candidate.experience.map((e, i) => <li key={i}>{(e.detail as string) ?? ""}</li>)
                ) : (
                  <li className="text-slate-400">Not detected</li>
                )}
              </ul>
            </div>
            <div className="card">
              <h3 className="mb-2 flex items-center gap-2 font-semibold">
                <GraduationCap size={16} /> Education
              </h3>
              <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-300">
                {candidate.education.length ? (
                  candidate.education.map((e, i) => <li key={i}>{(e.detail as string) ?? ""}</li>)
                ) : (
                  <li className="text-slate-400">Not detected</li>
                )}
              </ul>
            </div>
            <div className="card">
              <h3 className="mb-2 flex items-center gap-2 font-semibold">
                <Award size={16} /> Certifications
              </h3>
              <div className="flex flex-wrap gap-1">
                {candidate.certifications.length ? (
                  candidate.certifications.map((c, i) => <SkillChip key={i}>{c}</SkillChip>)
                ) : (
                  <span className="text-sm text-slate-400">None</span>
                )}
              </div>
            </div>
            <div className="card">
              <h3 className="mb-2 flex items-center gap-2 font-semibold">
                <Lightbulb size={16} /> Interview Questions
              </h3>
              <ol className="list-inside list-decimal space-y-1 text-sm text-slate-600 dark:text-slate-300">
                {score?.interview_questions.map((q, i) => <li key={i}>{q}</li>) ?? (
                  <li className="text-slate-400">Run analysis to generate</li>
                )}
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
