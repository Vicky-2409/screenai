import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, FileText, Loader2, UploadCloud, XCircle } from "lucide-react";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import toast from "react-hot-toast";
import { useNavigate, useParams } from "react-router-dom";

import { PageHeader, ProgressBar } from "@/components/ui";
import { apiErrorMessage } from "@/lib/api";
import { getJob } from "@/services/jobs";
import { getProgress, listResumes, uploadResumes } from "@/services/resumes";

export function UploadPage() {
  const { jobId } = useParams();
  const id = Number(jobId);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [files, setFiles] = useState<File[]>([]);
  const [uploadPercent, setUploadPercent] = useState(0);

  const { data: job } = useQuery({ queryKey: ["job", jobId], queryFn: () => getJob(id) });
  const { data: resumes } = useQuery({
    queryKey: ["resumes", id],
    queryFn: () => listResumes(id),
    // Keep polling while any resume is still being parsed/scored so the
    // per-file status labels update once the worker finishes.
    refetchInterval: (q) => {
      const data = q.state.data;
      const stillWorking = data?.some(
        (r) => r.status !== "scored" && r.status !== "failed",
      );
      return stillWorking ? 2000 : false;
    },
  });
  const { data: progress } = useQuery({
    queryKey: ["progress", id],
    queryFn: () => getProgress(id),
    refetchInterval: (q) => {
      const data = q.state.data;
      return data && data.pending > 0 ? 2000 : false;
    },
  });

  const onDrop = useCallback((accepted: File[]) => {
    setFiles((prev) => [...prev, ...accepted]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
    },
  });

  const uploadMutation = useMutation({
    mutationFn: () => uploadResumes(id, files, setUploadPercent),
    onSuccess: (res) => {
      toast.success(res.message);
      setFiles([]);
      setUploadPercent(0);
      void queryClient.invalidateQueries({ queryKey: ["resumes", id] });
      void queryClient.invalidateQueries({ queryKey: ["progress", id] });
    },
    onError: (err) => toast.error(apiErrorMessage(err, "Upload failed")),
  });

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        title="Upload Resumes"
        subtitle={job ? `For: ${job.title}` : "Drag and drop resumes to screen"}
        action={
          <button className="btn-secondary" onClick={() => navigate(`/jobs/${id}/candidates`)}>
            View Candidates
          </button>
        }
      />

      <div
        {...getRootProps()}
        className={`card flex cursor-pointer flex-col items-center justify-center border-2 border-dashed py-14 text-center transition ${
          isDragActive ? "border-brand-500 bg-brand-50 dark:bg-brand-600/10" : "border-slate-300 dark:border-slate-700"
        }`}
      >
        <input {...getInputProps()} />
        <UploadCloud className="mb-3 text-brand-500" size={40} />
        <p className="font-semibold">Drop resumes here or click to browse</p>
        <p className="mt-1 text-sm text-slate-500">PDF, DOCX, TXT - single or bulk (100+)</p>
      </div>

      {files.length > 0 && (
        <div className="card mt-4">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-semibold">{files.length} file(s) ready</h3>
            <div className="flex gap-2">
              <button className="btn-ghost" onClick={() => setFiles([])}>
                Clear
              </button>
              <button
                className="btn-primary"
                onClick={() => uploadMutation.mutate()}
                disabled={uploadMutation.isPending}
              >
                {uploadMutation.isPending ? <Loader2 className="animate-spin" size={16} /> : <UploadCloud size={16} />}
                Upload &amp; Screen
              </button>
            </div>
          </div>
          {uploadMutation.isPending && <ProgressBar value={uploadPercent} className="mb-3" />}
          <ul className="max-h-48 space-y-1 overflow-y-auto text-sm">
            {files.map((f, i) => (
              <li key={i} className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
                <FileText size={14} /> {f.name}{" "}
                <span className="text-xs text-slate-400">({(f.size / 1024).toFixed(0)} KB)</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {progress && progress.total > 0 && (
        <div className="card mt-4">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="font-semibold">Processing</h3>
            <span className="text-sm text-slate-500">
              {progress.scored}/{progress.total} scored
            </span>
          </div>
          <ProgressBar value={(progress.scored / progress.total) * 100} />
          <div className="mt-2 flex gap-4 text-xs text-slate-500">
            <span>Pending: {progress.pending}</span>
            <span>Failed: {progress.failed}</span>
          </div>
        </div>
      )}

      {resumes && resumes.length > 0 && (
        <div className="card mt-4">
          <h3 className="mb-3 font-semibold">Uploaded Resumes</h3>
          <ul className="space-y-2 text-sm">
            {resumes.map((r) => (
              <li key={r.id} className="flex items-center justify-between border-b border-slate-100 pb-2 last:border-0 dark:border-slate-800">
                <span className="flex items-center gap-2">
                  <FileText size={14} /> {r.original_filename}
                </span>
                <StatusIcon status={r.status} />
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function StatusIcon({ status }: { status: string }) {
  if (status === "scored")
    return (
      <span className="flex items-center gap-1 text-xs text-emerald-600">
        <CheckCircle2 size={14} /> Scored
      </span>
    );
  if (status === "failed")
    return (
      <span className="flex items-center gap-1 text-xs text-rose-500">
        <XCircle size={14} /> Failed
      </span>
    );
  return (
    <span className="flex items-center gap-1 text-xs text-amber-500">
      <Loader2 size={14} className="animate-spin" /> {status}
    </span>
  );
}
