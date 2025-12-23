import { X } from "lucide-react";
import { useState } from "react";

export function SkillsInput({
  value,
  onChange,
}: {
  value: string[];
  onChange: (skills: string[]) => void;
}) {
  const [draft, setDraft] = useState("");

  function add() {
    const cleaned = draft.trim().toLowerCase();
    if (cleaned && !value.includes(cleaned)) {
      onChange([...value, cleaned]);
    }
    setDraft("");
  }

  return (
    <div>
      <div className="flex flex-wrap gap-2 rounded-xl border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800">
        {value.map((skill) => (
          <span
            key={skill}
            className="badge inline-flex items-center gap-1 bg-brand-100 text-brand-700 dark:bg-brand-600/20 dark:text-brand-300"
          >
            {skill}
            <button type="button" onClick={() => onChange(value.filter((s) => s !== skill))}>
              <X size={12} />
            </button>
          </span>
        ))}
        <input
          className="min-w-[120px] flex-1 bg-transparent px-1 text-sm outline-none"
          value={draft}
          placeholder="Type a skill and press Enter"
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === ",") {
              e.preventDefault();
              add();
            }
          }}
          onBlur={add}
        />
      </div>
    </div>
  );
}
