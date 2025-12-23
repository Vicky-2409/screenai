import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Briefcase, MapPin, Plus, Trash2, Upload, Users } from "lucide-react";
import toast from "react-hot-toast";
import { Link, useNavigate } from "react-router-dom";

import { EmptyState, PageHeader, ScoreBadge, Skeleton } from "@/components/ui";
import { apiErrorMessage } from "@/lib/api";
import { deleteJob, listJobs } from "@/services/jobs";

export function JobsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: jobs, isLoading } = useQuery({ queryKey: ["jobs"], queryFn: listJobs });

  const removeMutation = useMutation({
    mutationFn: deleteJob,
    onSuccess: () => {
      toast.success("Job deleted");
      void queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
    onError: (err) => toast.error(apiErrorMessage(err)),
  });

  return (
    <div>
      <PageHeader
        title="Jobs"
        subtitle="Manage your open roles and screen candidates"
        action={
          <Link to="/jobs/new" className="btn-primary">
            <Plus size={16} /> Create Job
          </Link>
        }
      />

      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-44 rounded-2xl" />
          ))}
        </div>
      )}

      {!isLoading && jobs?.length === 0 && (
        <EmptyState
          icon={Briefcase}
          title="No jobs yet"
          description="Create your first job description to start screening resumes."
          action={
            <Link to="/jobs/new" className="btn-primary">
              <Plus size={16} /> Create Job
            </Link>
          }
        />
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {jobs?.map((job, i) => (
          <motion.div
            key={job.id}
            className="card flex flex-col"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04 }}
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold">{job.title}</h3>
                <p className="text-sm text-slate-500">{job.department || "General"}</p>
              </div>
              <span className="badge bg-brand-100 capitalize text-brand-700 dark:bg-brand-600/20 dark:text-brand-300">
                {job.status}
              </span>
            </div>

            <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-500">
              {job.location && (
                <span className="flex items-center gap-1">
                  <MapPin size={13} /> {job.location}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Users size={13} /> {job.resume_count ?? 0} resumes
              </span>
              {(job.average_score ?? 0) > 0 && <ScoreBadge score={job.average_score ?? 0} />}
            </div>

            <div className="mt-3 flex flex-wrap gap-1">
              {job.skills.slice(0, 5).map((s) => (
                <span key={s} className="badge bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                  {s}
                </span>
              ))}
            </div>

            <div className="mt-auto flex gap-2 pt-4">
              <button
                onClick={() => navigate(`/jobs/${job.id}/candidates`)}
                className="btn-secondary flex-1"
              >
                <Users size={15} /> Candidates
              </button>
              <button
                onClick={() => navigate(`/jobs/${job.id}/upload`)}
                className="btn-secondary"
                title="Upload resumes"
              >
                <Upload size={15} />
              </button>
              <button
                onClick={() => {
                  if (confirm(`Delete job "${job.title}"?`)) removeMutation.mutate(job.id);
                }}
                className="btn-ghost text-rose-500"
                title="Delete job"
              >
                <Trash2 size={15} />
              </button>
            </div>
            <Link to={`/jobs/${job.id}/edit`} className="mt-2 text-center text-xs text-slate-400 hover:text-brand-600">
              Edit job details
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
