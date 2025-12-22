import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import clsx from "clsx";

import type { CandidateStatus } from "@/types";

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

export function StatCard({
  label,
  value,
  icon: Icon,
  accent = "brand",
  index = 0,
}: {
  label: string;
  value: string | number;
  icon: LucideIcon;
  accent?: "brand" | "emerald" | "amber" | "sky" | "rose";
  index?: number;
}) {
  const accents: Record<string, string> = {
    brand: "bg-brand-100 text-brand-600 dark:bg-brand-600/20 dark:text-brand-300",
    emerald: "bg-emerald-100 text-emerald-600 dark:bg-emerald-600/20 dark:text-emerald-300",
    amber: "bg-amber-100 text-amber-600 dark:bg-amber-600/20 dark:text-amber-300",
    sky: "bg-sky-100 text-sky-600 dark:bg-sky-600/20 dark:text-sky-300",
    rose: "bg-rose-100 text-rose-600 dark:bg-rose-600/20 dark:text-rose-300",
  };
  return (
    <motion.div
      className="card flex items-center gap-4"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <div className={clsx("flex h-12 w-12 items-center justify-center rounded-xl", accents[accent])}>
        <Icon size={22} />
      </div>
      <div>
        <p className="text-sm text-slate-500 dark:text-slate-400">{label}</p>
        <p className="text-2xl font-bold">{value}</p>
      </div>
    </motion.div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={clsx("skeleton h-4 w-full", className)} />;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="card flex flex-col items-center justify-center py-14 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-400 dark:bg-slate-800">
        <Icon size={26} />
      </div>
      <h3 className="text-lg font-semibold">{title}</h3>
      {description && <p className="mt-1 max-w-sm text-sm text-slate-500">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 80
      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-600/20 dark:text-emerald-300"
      : score >= 60
        ? "bg-sky-100 text-sky-700 dark:bg-sky-600/20 dark:text-sky-300"
        : score >= 40
          ? "bg-amber-100 text-amber-700 dark:bg-amber-600/20 dark:text-amber-300"
          : "bg-rose-100 text-rose-700 dark:bg-rose-600/20 dark:text-rose-300";
  return <span className={clsx("badge font-semibold", color)}>{score.toFixed(0)}%</span>;
}

const STATUS_STYLES: Record<CandidateStatus, string> = {
  new: "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300",
  shortlisted: "bg-emerald-100 text-emerald-700 dark:bg-emerald-600/20 dark:text-emerald-300",
  rejected: "bg-rose-100 text-rose-700 dark:bg-rose-600/20 dark:text-rose-300",
  interviewing: "bg-sky-100 text-sky-700 dark:bg-sky-600/20 dark:text-sky-300",
  hired: "bg-brand-100 text-brand-700 dark:bg-brand-600/20 dark:text-brand-300",
};

export function StatusBadge({ status }: { status: CandidateStatus }) {
  return (
    <span className={clsx("badge capitalize", STATUS_STYLES[status])}>
      {status.replace("_", " ")}
    </span>
  );
}

export function SkillChip({ children, variant = "default" }: { children: ReactNode; variant?: "default" | "match" | "missing" }) {
  const styles = {
    default: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
    match: "bg-emerald-100 text-emerald-700 dark:bg-emerald-600/20 dark:text-emerald-300",
    missing: "bg-rose-100 text-rose-700 dark:bg-rose-600/20 dark:text-rose-300",
  };
  return <span className={clsx("badge", styles[variant])}>{children}</span>;
}

export function ProgressBar({ value, className }: { value: number; className?: string }) {
  return (
    <div className={clsx("h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700", className)}>
      <motion.div
        className="h-full rounded-full bg-brand-600"
        initial={{ width: 0 }}
        animate={{ width: `${Math.min(100, value)}%` }}
        transition={{ duration: 0.5 }}
      />
    </div>
  );
}
