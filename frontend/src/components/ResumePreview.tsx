import { Download, FileText, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import { fetchResumeBlobUrl } from "@/services/resumes";

export function ResumePreview({ resumeId, filename }: { resumeId: number; filename?: string }) {
  const [url, setUrl] = useState<string | null>(null);
  const [contentType, setContentType] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let revoked: string | null = null;
    setLoading(true);
    fetchResumeBlobUrl(resumeId)
      .then(({ url, contentType }) => {
        revoked = url;
        setUrl(url);
        setContentType(contentType);
      })
      .catch(() => toast.error("Could not load resume file"))
      .finally(() => setLoading(false));
    return () => {
      if (revoked) URL.revokeObjectURL(revoked);
    };
  }, [resumeId]);

  const isPdf = contentType.includes("pdf");

  function download() {
    if (!url) return;
    const a = document.createElement("a");
    a.href = url;
    a.download = filename ?? `resume_${resumeId}`;
    a.click();
  }

  return (
    <div className="card">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="flex items-center gap-2 font-semibold">
          <FileText size={16} /> Resume Preview
        </h3>
        <button className="btn-secondary" onClick={download} disabled={!url}>
          <Download size={14} /> Download
        </button>
      </div>

      {loading && (
        <div className="flex h-40 items-center justify-center text-slate-400">
          <Loader2 className="animate-spin" size={22} />
        </div>
      )}

      {!loading && url && isPdf && (
        <iframe title="Resume preview" src={url} className="h-[480px] w-full rounded-lg border border-slate-200 dark:border-slate-700" />
      )}

      {!loading && url && !isPdf && (
        <p className="text-sm text-slate-500">
          Inline preview is available for PDFs. Use Download to open this {filename ? `(${filename})` : "file"}.
        </p>
      )}
    </div>
  );
}
