import type { LiveStatus } from "@/lib/live/use-live-team";
import { cn } from "@/lib/utils";

const LIVE_STATUS: Record<LiveStatus, { label: string; dot: string }> = {
  connecting: { label: "Connecting…", dot: "bg-muted-foreground" },
  live: { label: "Live", dot: "bg-emerald-500" },
  reconnecting: { label: "Reconnecting…", dot: "bg-amber-500" },
};

export function LiveIndicator({ status }: { status: LiveStatus }) {
  const { label, dot } = LIVE_STATUS[status];
  return (
    <span role="status" className="flex items-center gap-1.5 text-xs text-muted-foreground">
      <span aria-hidden className={cn("size-2 rounded-full", dot)} />
      {label}
    </span>
  );
}
