import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Briefcase, FileText, HardDrive, ShieldAlert, Users } from "lucide-react";
import { Navigate } from "react-router-dom";

import { PageHeader, ProgressBar, Skeleton, StatCard } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";
import {
  getAdminStats,
  getStorageStats,
  listLogs,
  listUsers,
  toggleUserActive,
} from "@/services/admin";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let value = bytes / 1024;
  let i = 0;
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024;
    i++;
  }
  return `${value.toFixed(1)} ${units[i]}`;
}

export function AdminPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const { data: stats, isLoading } = useQuery({
    queryKey: ["admin-stats"],
    queryFn: getAdminStats,
    enabled: user?.role === "admin",
  });
  const { data: users } = useQuery({
    queryKey: ["admin-users"],
    queryFn: listUsers,
    enabled: user?.role === "admin",
  });
  const { data: logs } = useQuery({
    queryKey: ["admin-logs"],
    queryFn: listLogs,
    enabled: user?.role === "admin",
  });
  const { data: storage } = useQuery({
    queryKey: ["admin-storage"],
    queryFn: getStorageStats,
    enabled: user?.role === "admin",
  });

  const toggle = useMutation({
    mutationFn: toggleUserActive,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });

  if (user && user.role !== "admin") {
    return <Navigate to="/" replace />;
  }

  return (
    <div>
      <PageHeader title="Admin Panel" subtitle="Platform-wide management and audit logs" />

      {isLoading || !stats ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-2xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard label="Users" value={stats.total_users} icon={Users} accent="brand" />
          <StatCard label="Jobs" value={stats.total_jobs} icon={Briefcase} accent="sky" />
          <StatCard label="Resumes" value={stats.total_resumes} icon={FileText} accent="emerald" />
          <StatCard label="Candidates" value={stats.total_candidates} icon={Users} accent="amber" />
        </div>
      )}

      {storage && (
        <div className="card mt-6">
          <h3 className="mb-3 flex items-center gap-2 font-semibold">
            <HardDrive size={16} /> Storage
          </h3>
          <div className="flex flex-wrap items-baseline gap-x-6 gap-y-1 text-sm">
            <span>
              <span className="text-2xl font-bold">{formatBytes(storage.total_bytes)}</span>{" "}
              <span className="text-slate-500">used</span>
            </span>
            <span className="text-slate-500">{storage.total_files} files</span>
          </div>
          {storage.breakdown.length > 0 && (
            <div className="mt-4 space-y-3">
              {storage.breakdown.map((b) => (
                <div key={b.label}>
                  <div className="mb-1 flex justify-between text-xs text-slate-500">
                    <span className="font-medium text-slate-600 dark:text-slate-300">
                      {b.label} ({b.files})
                    </span>
                    <span>{formatBytes(b.bytes)}</span>
                  </div>
                  <ProgressBar
                    value={storage.total_bytes ? (b.bytes / storage.total_bytes) * 100 : 0}
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h3 className="mb-3 font-semibold">Users</h3>
          <div className="space-y-2">
            {users?.map((u) => (
              <div
                key={u.id}
                className="flex items-center justify-between border-b border-slate-100 pb-2 text-sm last:border-0 dark:border-slate-800"
              >
                <div>
                  <p className="font-medium">{u.full_name}</p>
                  <p className="text-xs text-slate-400">
                    {u.email} - {u.role}
                  </p>
                </div>
                <button
                  className={`badge ${u.is_active ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"}`}
                  onClick={() => toggle.mutate(u.id)}
                >
                  {u.is_active ? "Active" : "Inactive"}
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h3 className="mb-3 flex items-center gap-2 font-semibold">
            <ShieldAlert size={16} /> Audit Logs
          </h3>
          <div className="max-h-96 space-y-2 overflow-y-auto">
            {logs?.map((log) => (
              <div key={log.id} className="border-b border-slate-100 pb-2 text-sm last:border-0 dark:border-slate-800">
                <p>{log.message ?? log.action}</p>
                <p className="text-xs text-slate-400">{new Date(log.created_at).toLocaleString()}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
