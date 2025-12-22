import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell } from "lucide-react";
import { useState } from "react";

import { listNotifications, markAllNotificationsRead } from "@/services/misc";
import clsx from "clsx";

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();
  const { data } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => listNotifications(),
    refetchInterval: 20_000,
  });

  const unread = (data ?? []).filter((n) => !n.read).length;

  async function handleReadAll() {
    await markAllNotificationsRead();
    void queryClient.invalidateQueries({ queryKey: ["notifications"] });
  }

  return (
    <div className="relative">
      <button className="btn-ghost relative p-2" onClick={() => setOpen((o) => !o)}>
        <Bell size={18} />
        {unread > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
            {unread}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-80 rounded-xl border border-slate-200 bg-white shadow-lg dark:border-slate-700 dark:bg-slate-800">
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-2 dark:border-slate-700">
            <span className="text-sm font-semibold">Notifications</span>
            <button className="text-xs text-brand-600" onClick={handleReadAll}>
              Mark all read
            </button>
          </div>
          <div className="max-h-80 overflow-y-auto">
            {(data ?? []).length === 0 && (
              <p className="px-4 py-6 text-center text-sm text-slate-400">No notifications</p>
            )}
            {(data ?? []).map((n) => (
              <div
                key={n.id}
                className={clsx(
                  "border-b border-slate-50 px-4 py-3 last:border-0 dark:border-slate-700/50",
                  !n.read && "bg-brand-50/60 dark:bg-brand-600/10",
                )}
              >
                <p className="text-sm font-medium">{n.title}</p>
                {n.message && <p className="text-xs text-slate-500">{n.message}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
