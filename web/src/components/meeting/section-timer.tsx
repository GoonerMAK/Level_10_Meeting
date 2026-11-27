"use client";

import { AlarmClock, Timer } from "lucide-react";

import { useServerNow } from "@/components/meeting/use-server-now";
import { formatClock, sectionTime } from "@/lib/meeting-clock";
import { cn } from "@/lib/utils";

type SectionTimerProps = { sectionLabel: string; startedAt: string; endsAt: string };

export function SectionTimer({ sectionLabel, startedAt, endsAt }: SectionTimerProps) {
  const { overTime, seconds } = sectionTime({ startedAt, endsAt }, useServerNow());
  const clock = formatClock(seconds);
  const Icon = overTime ? AlarmClock : Timer;

  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-md px-4 py-2",
        overTime ? "bg-red-100 text-red-900" : "bg-muted text-foreground",
      )}
    >
      <Icon aria-hidden className="size-6 shrink-0" />
      <div
        role="timer"
        aria-label={overTime ? `${sectionLabel} over time by ${clock}` : `${clock} left in ${sectionLabel}`}
        className="flex items-baseline gap-2"
      >
        {overTime && <span className="text-sm font-semibold uppercase">Over time</span>}
        <span className="font-mono text-3xl font-semibold tabular-nums">
          {overTime ? `+${clock}` : clock}
        </span>
        {!overTime && <span className="text-sm text-muted-foreground">left</span>}
      </div>
      <p role="alert" className="sr-only">
        {overTime ? `${sectionLabel} is over time` : ""}
      </p>
    </div>
  );
}
