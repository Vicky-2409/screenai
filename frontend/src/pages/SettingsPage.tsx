import { Moon, Sun } from "lucide-react";

import { PageHeader } from "@/components/ui";
import { useTheme } from "@/context/ThemeContext";

export function SettingsPage() {
  const { theme, toggle } = useTheme();

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader title="Settings" subtitle="Customize your experience" />

      <div className="card">
        <h3 className="font-semibold">Appearance</h3>
        <p className="text-sm text-slate-500">Switch between light and dark mode</p>
        <button className="btn-secondary mt-3" onClick={toggle}>
          {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
          {theme === "dark" ? "Switch to light" : "Switch to dark"}
        </button>
      </div>

      <div className="card mt-4">
        <h3 className="font-semibold">Scoring Weights</h3>
        <p className="text-sm text-slate-500">
          Candidates are ranked using a weighted blend of signals:
        </p>
        <ul className="mt-3 space-y-1 text-sm text-slate-600 dark:text-slate-300">
          <li>Semantic similarity - 40%</li>
          <li>Skill match - 25%</li>
          <li>Experience match - 20%</li>
          <li>Education match - 10%</li>
          <li>Keyword match - 5%</li>
        </ul>
      </div>
    </div>
  );
}
