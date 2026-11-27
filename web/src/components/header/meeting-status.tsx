"use client";

import { Badge } from "@/components/ui/badge";
import type { Schemas } from "@/lib/api/client";
import { useActiveMeeting } from "@/lib/api/teams";

const SECTION_LABELS: Record<Schemas["MeetingSection"], string> = {
  scorecard: "Scorecard",
  ids: "IDS",
  conclude: "Conclude",
};

export function MeetingStatus({ teamId }: { teamId: string }) {
  const meeting = useActiveMeeting(teamId);
  if (!meeting.data || meeting.data.ended_at) {
    return null;
  }
  const section = meeting.data.section ? ` · ${SECTION_LABELS[meeting.data.section]}` : "";
  return (
    <Badge variant="secondary" className="gap-1.5">
      <span aria-hidden className="size-2 animate-pulse rounded-full bg-emerald-500" />
      Meeting in progress{section}
    </Badge>
  );
}
