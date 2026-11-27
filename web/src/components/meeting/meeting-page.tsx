"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { useCurrentUser } from "@/components/auth/require-sign-in";
import { IssueDrawer } from "@/components/issues/issue-drawer";
import { IssuesSection } from "@/components/issues/issues-section";
import { AgendaSteps } from "@/components/meeting/agenda-steps";
import { AttendeeList } from "@/components/meeting/attendee-list";
import { ConcludeSection } from "@/components/meeting/conclude-section";
import { FacilitatorControls } from "@/components/meeting/facilitator-controls";
import { MeetingSummaryView } from "@/components/meeting/meeting-summary";
import { SectionTimer } from "@/components/meeting/section-timer";
import { PageSkeleton } from "@/components/page-skeleton";
import { ScorecardSection } from "@/components/scorecard/scorecard-section";
import { useTeamContext } from "@/components/team/team-context";
import { Button } from "@/components/ui/button";
import type { MeetingState } from "@/lib/api/client";
import { errorMessage } from "@/lib/api/errors";
import { useJoinMeeting, useStartMeeting } from "@/lib/api/meetings";
import { useActiveMeeting } from "@/lib/api/teams";
import { SECTION_LABELS, type MeetingSection } from "@/lib/meeting-clock";

export function MeetingPage() {
  const { teamId } = useTeamContext();
  const meeting = useActiveMeeting(teamId);
  const [seenMeetingId, setSeenMeetingId] = useState<string | null>(null);

  if (meeting.data && meeting.data.id !== seenMeetingId) {
    setSeenMeetingId(meeting.data.id);
  }

  const renderContent = () => {
    if (meeting.isPending) {
      return <PageSkeleton />;
    }
    const running = meeting.data && !meeting.data.ended_at ? meeting.data : null;
    if (running?.section && running.section_started_at && running.section_ends_at) {
      return (
        <MeetingRoom
          key={running.id}
          meeting={running}
          section={running.section}
          startedAt={running.section_started_at}
          endsAt={running.section_ends_at}
        />
      );
    }
    const endedMeetingId = meeting.data?.id ?? seenMeetingId;
    if (endedMeetingId) {
      return <MeetingSummaryView meetingId={endedMeetingId} />;
    }
    return <NoMeeting />;
  };

  return (
    <>
      {renderContent()}
      <IssueDrawer />
    </>
  );
}

type MeetingRoomProps = { meeting: MeetingState; section: MeetingSection; startedAt: string; endsAt: string };

function MeetingRoom({ meeting, section, startedAt, endsAt }: MeetingRoomProps) {
  const me = useCurrentUser();
  const joinMeeting = useJoinMeeting(meeting.team_id);
  const joined = meeting.attendees.some((attendee) => attendee.id === me.id);
  const isFacilitator = meeting.facilitator.id === me.id;
  const { mutate: join, isIdle: joinNotTried } = joinMeeting;

  useEffect(() => {
    if (!joined && joinNotTried) {
      join(meeting.id, { onError: (error) => toast.error(errorMessage(error)) });
    }
  }, [joined, joinNotTried, join, meeting.id]);

  return (
    <div className="flex flex-col gap-6">
      <div className="sticky top-0 z-20 -mx-4 flex flex-col gap-3 border-b bg-background/95 px-4 py-3 shadow-sm backdrop-blur lg:-mx-6 lg:px-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-col gap-2">
            <h1 className="text-2xl font-semibold">{SECTION_LABELS[section]}</h1>
            <AgendaSteps section={section} />
          </div>
          <SectionTimer sectionLabel={SECTION_LABELS[section]} startedAt={startedAt} endsAt={endsAt} />
          {isFacilitator ? (
            <FacilitatorControls meeting={meeting} section={section} />
          ) : (
            <p className="text-sm text-muted-foreground">{meeting.facilitator.name} runs this meeting</p>
          )}
        </div>
        <AttendeeList meeting={meeting} meId={me.id} />
      </div>
      <SectionContent meeting={meeting} section={section} />
    </div>
  );
}

function SectionContent({ meeting, section }: { meeting: MeetingState; section: MeetingSection }) {
  switch (section) {
    case "scorecard":
      return <ScorecardSection />;
    case "ids":
      return <IssuesSection />;
    case "conclude":
      return <ConcludeSection meeting={meeting} />;
    default: {
      const exhaustive: never = section;
      return exhaustive;
    }
  }
}

function NoMeeting() {
  const { teamId, teamName, canChange } = useTeamContext();
  const startMeeting = useStartMeeting(teamId);

  return (
    <div className="flex flex-col items-start gap-3 rounded-lg border bg-card p-6">
      <h1 className="text-2xl font-semibold">No meeting running for {teamName}</h1>
      {canChange ? (
        <Button
          size="lg"
          disabled={startMeeting.isPending}
          onClick={() => startMeeting.mutate(undefined, { onError: (error) => toast.error(errorMessage(error)) })}
        >
          Start meeting
        </Button>
      ) : (
        <p className="text-sm text-muted-foreground">
          This page joins the meeting as soon as an Admin or Team Member starts it.
        </p>
      )}
    </div>
  );
}
