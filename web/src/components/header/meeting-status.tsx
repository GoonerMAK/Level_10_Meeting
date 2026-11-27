"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { toast } from "sonner";

import { useCurrentUser } from "@/components/auth/require-sign-in";
import { Button } from "@/components/ui/button";
import { errorMessage } from "@/lib/api/errors";
import { useStartMeeting } from "@/lib/api/meetings";
import { useActiveMeeting } from "@/lib/api/teams";
import { SECTION_LABELS } from "@/lib/meeting-clock";
import { canChangeTeam } from "@/lib/permissions";
import { meetingPath } from "@/lib/routes";

export function MeetingStatus({ teamId }: { teamId: string }) {
  const me = useCurrentUser();
  const meeting = useActiveMeeting(teamId);
  const startMeeting = useStartMeeting(teamId);
  const router = useRouter();
  const pathname = usePathname();

  if (pathname === meetingPath(teamId) || meeting.isPending) {
    return null;
  }

  const running = meeting.data && !meeting.data.ended_at ? meeting.data : null;
  if (running) {
    const joined = running.attendees.some((attendee) => attendee.id === me.id);
    const section = running.section ? ` · ${SECTION_LABELS[running.section]}` : "";
    return (
      <Button asChild size="sm">
        <Link href={meetingPath(teamId)}>
          <span aria-hidden className="size-2 animate-pulse rounded-full bg-emerald-400" />
          {joined ? "Back to meeting" : "Join meeting"}
          {section}
        </Link>
      </Button>
    );
  }

  if (!canChangeTeam(me, teamId)) {
    return null;
  }

  const start = () =>
    startMeeting.mutate(undefined, {
      onSuccess: () => router.push(meetingPath(teamId)),
      onError: (error) => toast.error(errorMessage(error)),
    });

  return (
    <Button size="sm" onClick={start} disabled={startMeeting.isPending}>
      Start meeting
    </Button>
  );
}
