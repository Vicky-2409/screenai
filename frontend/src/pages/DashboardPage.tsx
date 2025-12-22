import { useQuery } from "@tanstack/react-query";
import { Activity, Briefcase, Clock, FileText, Gauge, Users } from "lucide-react";
import {
  Bar,
  BarChart,
  Cell,
  Funnel,
  FunnelChart,
  LabelList,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { PageHeader, Skeleton, StatCard } from "@/components/ui";
import { getDashboard } from "@/services/misc";

const PIE_COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#0ea5e9", "#ef4444", "#a855f7", "#14b8a6", "#ec4899"];

export function DashboardPage() {
  const { data, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: getDashboard });

  if (isLoading || !data) {
    return (
      <div>
        <PageHeader title="Dashboard" subtitle="Your recruiting overview" />
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-2xl" />
          ))}
        </div>
      </div>
    );
  }

  const { stats } = data;

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Your recruiting overview at a glance" />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <StatCard label="Total Jobs" value={stats.total_jobs} icon={Briefcase} accent="brand" index={0} />
        <StatCard label="Resumes" value={stats.total_resumes} icon={FileText} accent="sky" index={1} />
        <StatCard label="Screened" value={stats.candidates_screened} icon={Users} accent="emerald" index={2} />
        <StatCard
          label="Avg Match"
          value={`${stats.average_match_score.toFixed(0)}%`}
          icon={Gauge}
          accent="amber"
          index={3}
        />
        <StatCard label="In Queue" value={stats.processing_queue} icon={Clock} accent="rose" index={4} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h3 className="mb-4 font-semibold">Candidate Score Distribution</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.score_distribution}>
              <XAxis dataKey="label" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip cursor={{ fill: "rgba(99,102,241,0.08)" }} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]} fill="#6366f1" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 className="mb-4 font-semibold">Skill Distribution</h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={data.skill_distribution}
                dataKey="value"
                nameKey="label"
                outerRadius={95}
                label={(e) => e.label}
              >
                {data.skill_distribution.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 className="mb-4 font-semibold">Top Skills</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.top_skills} layout="vertical">
              <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
              <YAxis type="category" dataKey="label" width={90} tick={{ fontSize: 12 }} />
              <Tooltip cursor={{ fill: "rgba(34,197,94,0.08)" }} />
              <Bar dataKey="value" radius={[0, 6, 6, 0]} fill="#22c55e" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 className="mb-4 font-semibold">Hiring Funnel</h3>
          <ResponsiveContainer width="100%" height={260}>
            <FunnelChart>
              <Tooltip />
              <Funnel dataKey="value" data={data.hiring_funnel} isAnimationActive>
                <LabelList position="right" fill="currentColor" stroke="none" dataKey="label" />
                {data.hiring_funnel.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Funnel>
            </FunnelChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <div className="card lg:col-span-2">
          <h3 className="mb-4 flex items-center gap-2 font-semibold">
            <Activity size={18} /> Recent Activity
          </h3>
          <ul className="space-y-3">
            {data.recent_activity.length === 0 && (
              <li className="text-sm text-slate-400">No activity yet.</li>
            )}
            {data.recent_activity.map((a, i) => (
              <li key={i} className="flex items-center justify-between border-b border-slate-100 pb-2 text-sm last:border-0 dark:border-slate-800">
                <span>{(a.message as string) ?? (a.action as string)}</span>
                <span className="text-xs text-slate-400">
                  {new Date(a.created_at as string).toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="card flex flex-col items-center justify-center text-center">
          <Clock className="text-brand-600" size={32} />
          <p className="mt-3 text-4xl font-bold">{data.time_saved_hours}h</p>
          <p className="text-sm text-slate-500">Estimated recruiter time saved</p>
        </div>
      </div>
    </div>
  );
}
