import { Mail, Shield, User as UserIcon } from "lucide-react";

import { PageHeader } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";

export function ProfilePage() {
  const { user } = useAuth();
  if (!user) return null;

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader title="Profile" subtitle="Your account details" />

      <div className="card">
        <div className="flex items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-600 text-2xl font-bold text-white">
            {user.full_name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h3 className="text-lg font-semibold">{user.full_name}</h3>
            <span className="badge bg-brand-100 capitalize text-brand-700 dark:bg-brand-600/20 dark:text-brand-300">
              {user.role}
            </span>
          </div>
        </div>

        <ul className="mt-6 space-y-3 text-sm">
          <li className="flex items-center gap-3 text-slate-600 dark:text-slate-300">
            <UserIcon size={16} /> {user.full_name}
          </li>
          <li className="flex items-center gap-3 text-slate-600 dark:text-slate-300">
            <Mail size={16} /> {user.email}
          </li>
          <li className="flex items-center gap-3 text-slate-600 dark:text-slate-300">
            <Shield size={16} /> Account {user.is_active ? "active" : "inactive"}
          </li>
        </ul>
      </div>
    </div>
  );
}
