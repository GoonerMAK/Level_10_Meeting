"use client";

import { toast } from "sonner";

import { useCurrentUser } from "@/components/auth/require-sign-in";
import { ErrorState } from "@/components/error-state";
import { SummaryTodoList } from "@/components/meeting/summary-lists";
import { SectionCard } from "@/components/section-card";
import { useTeamContext } from "@/components/team/team-context";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { MeetingState } from "@/lib/api/client";
import { errorMessage } from "@/lib/api/errors";
import { useMeetingSummary, useRateMeeting } from "@/lib/api/meetings";
import { formatRating } from "@/lib/format";
import { cn } from "@/lib/utils";

const RATINGS = Array.from({ length: 10 }, (_, index) => index + 1);

export function ConcludeSection({ meeting }: { meeting: MeetingState }) {
  return (
    <div className="grid items-start gap-6 lg:grid-cols-2">
      <NewTodos meeting={meeting} />
      <Ratings meeting={meeting} />
    </div>
  );
}

function NewTodos({ meeting }: { meeting: MeetingState }) {
  const summary = useMeetingSummary(meeting.team_id, meeting.id, "so-far");

  const renderBody = () => {
    if (summary.isPending) {
      return <Skeleton aria-label="Loading new To-Dos" className="h-24 w-full" />;
    }
    if (summary.isError) {
      return <ErrorState message={errorMessage(summary.error)} onRetry={() => void summary.refetch()} />;
    }
    return <SummaryTodoList todos={summary.data.todos_created} empty="No To-Dos were added in this meeting." />;
  };

  return (
    <SectionCard title="New To-Dos" description="Added since the meeting started">
      {renderBody()}
    </SectionCard>
  );
}

function Ratings({ meeting }: { meeting: MeetingState }) {
  const me = useCurrentUser();
  const { canChange, members } = useTeamContext();
  const isObserver = (userId: string) => members.some((member) => member.id === userId && member.role === "observer");
  const raters = meeting.attendees.filter((attendee) => !isObserver(attendee.id));
  const ratingOf = (userId: string) => meeting.ratings.find((entry) => entry.user.id === userId)?.rating ?? null;
  const waitingOn = raters.filter((rater) => ratingOf(rater.id) === null);
  const canRate = canChange && meeting.attendees.some((attendee) => attendee.id === me.id);

  return (
    <SectionCard
      title="Rate this meeting"
      description="1 to 10. You can change it until the meeting ends."
      actions={
        <p className="text-right">
          <span className="block text-3xl font-semibold tabular-nums">
            {meeting.rating === null ? "–" : formatRating(meeting.rating)}
          </span>
          <span className="text-xs text-muted-foreground">
            {meeting.rating === null ? "No ratings yet" : `Average of ${meeting.ratings.length}`}
          </span>
        </p>
      }
    >
      <div className="flex flex-col gap-4">
        {canRate ? (
          <RatingPicker meeting={meeting} current={ratingOf(me.id)} />
        ) : (
          <p className="text-sm text-muted-foreground">Observers follow along but don&apos;t rate.</p>
        )}
        <ul aria-label="Ratings" className="flex flex-col divide-y text-sm">
          {raters.map((rater) => {
            const rating = ratingOf(rater.id);
            return (
              <li key={rater.id} className="flex items-center justify-between py-2">
                <span>
                  {rater.name}
                  {rater.id === me.id && " (you)"}
                </span>
                <span className={cn("tabular-nums", rating === null && "text-muted-foreground")}>
                  {rating ?? "Not rated yet"}
                </span>
              </li>
            );
          })}
        </ul>
        {waitingOn.length > 0 && (
          <p className="text-sm text-muted-foreground">
            Waiting on {waitingOn.map((rater) => rater.name).join(", ")}
          </p>
        )}
      </div>
    </SectionCard>
  );
}

function RatingPicker({ meeting, current }: { meeting: MeetingState; current: number | null }) {
  const rateMeeting = useRateMeeting(meeting.team_id);

  const rate = (rating: number) =>
    rateMeeting.mutate({ meetingId: meeting.id, rating }, { onError: (error) => toast.error(errorMessage(error)) });

  return (
    <div role="group" aria-label="Your rating" className="grid grid-cols-10 gap-1.5">
      {RATINGS.map((rating) => (
        <Button
          key={rating}
          type="button"
          size="lg"
          variant={rating === current ? "default" : "outline"}
          aria-pressed={rating === current}
          disabled={rateMeeting.isPending}
          onClick={() => rate(rating)}
          className="px-0 tabular-nums"
        >
          {rating}
        </Button>
      ))}
    </div>
  );
}
