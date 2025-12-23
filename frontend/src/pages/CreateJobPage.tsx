import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Save } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useNavigate, useParams } from "react-router-dom";

import { RichTextEditor } from "@/components/RichTextEditor";
import { SkillsInput } from "@/components/SkillsInput";
import { PageHeader } from "@/components/ui";
import { apiErrorMessage } from "@/lib/api";
import { createJob, getJob, updateJob } from "@/services/jobs";
import type { EmploymentType, JobInput } from "@/types";

const EMPLOYMENT_TYPES: EmploymentType[] = [
  "full_time",
  "part_time",
  "contract",
  "internship",
  "temporary",
];

const EMPTY: JobInput = {
  title: "",
  department: "",
  location: "",
  experience: "",
  min_experience_years: 0,
  salary: "",
  employment_type: "full_time",
  description: "",
  responsibilities: "",
  qualifications: "",
  skills: [],
};

export function CreateJobPage() {
  const { jobId } = useParams();
  const isEdit = Boolean(jobId);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [form, setForm] = useState<JobInput>(EMPTY);

  const { data: existing } = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => getJob(Number(jobId)),
    enabled: isEdit,
  });

  useEffect(() => {
    if (existing) {
      setForm({
        title: existing.title,
        department: existing.department ?? "",
        location: existing.location ?? "",
        experience: existing.experience ?? "",
        min_experience_years: existing.min_experience_years,
        salary: existing.salary ?? "",
        employment_type: existing.employment_type,
        description: existing.description ?? "",
        responsibilities: existing.responsibilities ?? "",
        qualifications: existing.qualifications ?? "",
        skills: existing.skills,
      });
    }
  }, [existing]);

  const mutation = useMutation({
    mutationFn: (payload: JobInput) =>
      isEdit ? updateJob(Number(jobId), payload) : createJob(payload),
    onSuccess: (job) => {
      toast.success(isEdit ? "Job updated" : "Job created");
      void queryClient.invalidateQueries({ queryKey: ["jobs"] });
      navigate(isEdit ? "/jobs" : `/jobs/${job.id}/upload`);
    },
    onError: (err) => toast.error(apiErrorMessage(err)),
  });

  function set<K extends keyof JobInput>(key: K, val: JobInput[K]) {
    setForm((f) => ({ ...f, [key]: val }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.title.trim()) {
      toast.error("Title is required");
      return;
    }
    mutation.mutate(form);
  }

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title={isEdit ? "Edit Job" : "Create Job"} subtitle="Define the role to screen against" />

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="card grid gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label className="label">Title *</label>
            <input className="input" value={form.title} onChange={(e) => set("title", e.target.value)} required />
          </div>
          <div>
            <label className="label">Department</label>
            <input className="input" value={form.department} onChange={(e) => set("department", e.target.value)} />
          </div>
          <div>
            <label className="label">Location</label>
            <input className="input" value={form.location} onChange={(e) => set("location", e.target.value)} />
          </div>
          <div>
            <label className="label">Experience (text)</label>
            <input
              className="input"
              placeholder="e.g. 5-7 years"
              value={form.experience}
              onChange={(e) => set("experience", e.target.value)}
            />
          </div>
          <div>
            <label className="label">Minimum Experience (years)</label>
            <input
              type="number"
              min={0}
              step={0.5}
              className="input"
              value={form.min_experience_years}
              onChange={(e) => set("min_experience_years", Number(e.target.value))}
            />
          </div>
          <div>
            <label className="label">Salary</label>
            <input className="input" value={form.salary} onChange={(e) => set("salary", e.target.value)} />
          </div>
          <div>
            <label className="label">Employment Type</label>
            <select
              className="input"
              value={form.employment_type}
              onChange={(e) => set("employment_type", e.target.value as EmploymentType)}
            >
              {EMPLOYMENT_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.replace("_", " ")}
                </option>
              ))}
            </select>
          </div>
          <div className="sm:col-span-2">
            <label className="label">Required Skills</label>
            <SkillsInput value={form.skills ?? []} onChange={(s) => set("skills", s)} />
          </div>
        </div>

        <div className="card space-y-4">
          <div>
            <label className="label">Description</label>
            <RichTextEditor
              value={form.description ?? ""}
              onChange={(html) => set("description", html)}
              placeholder="Role overview..."
            />
          </div>
          <div>
            <label className="label">Responsibilities</label>
            <RichTextEditor
              value={form.responsibilities ?? ""}
              onChange={(html) => set("responsibilities", html)}
              placeholder="Key responsibilities..."
            />
          </div>
          <div>
            <label className="label">Qualifications</label>
            <RichTextEditor
              value={form.qualifications ?? ""}
              onChange={(html) => set("qualifications", html)}
              placeholder="Required qualifications..."
            />
          </div>
        </div>

        <div className="flex justify-end gap-3">
          <button type="button" className="btn-secondary" onClick={() => navigate("/jobs")}>
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
            {isEdit ? "Save changes" : "Create job"}
          </button>
        </div>
      </form>
    </div>
  );
}
