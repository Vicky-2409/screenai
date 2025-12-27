import { useQuery } from "@tanstack/react-query";
import { Download, FileSpreadsheet, FileText } from "lucide-react";
import toast from "react-hot-toast";

import { EmptyState, PageHeader, Skeleton } from "@/components/ui";
import { listJobs } from "@/services/jobs";
import { downloadReport } from "@/services/misc";

export function ReportsPage() {
  const { data: jobs, isLoading } = useQuery({ queryKey: ["jobs"], queryFn: listJobs });

  async function handleDownload(jobId: number, kind: "pdf" | "csv") {
    try {
      await downloadReport(jobId, kind);
      toast.success(`${kind.toUpperCase()} downloaded`);
    } catch {
      toast.error("Failed to generate report");
    }
  }

  return (
    <div>
      <PageHeader title="Reports" subtitle="Export candidate rankings and analysis" />

      {isLoading && <Skeleton className="h-40 rounded-2xl" />}

      {!isLoading && jobs?.length === 0 && (
        <EmptyState icon={FileText} title="No jobs to report on" description="Create a job and screen candidates first." />
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {jobs?.map((job) => (
          <div key={job.id} className="card">
            <h3 className="font-semibold">{job.title}</h3>
            <p className="text-sm text-slate-500">
              {job.scored_count ?? 0} scored - avg {(job.average_score ?? 0).toFixed(0)}%
            </p>
            <div className="mt-4 flex gap-2">
              <button className="btn-secondary flex-1" onClick={() => handleDownload(job.id, "pdf")}>
                <FileText size={15} /> PDF
              </button>
              <button className="btn-secondary flex-1" onClick={() => handleDownload(job.id, "csv")}>
                <FileSpreadsheet size={15} /> CSV
              </button>
            </div>
          </div>
        ))}
      </div>

      {jobs && jobs.length > 0 && (
        <div className="card mt-6 flex items-center gap-3 text-sm text-slate-500">
          <Download size={18} className="text-brand-500" />
          Reports include ranked candidates, skill-gap analysis, scores, and AI recommendations.
        </div>
      )}
    </div>
  );
}
