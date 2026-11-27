"use client";

import Link from "next/link";

import { ErrorState } from "@/components/error-state";
import { SummaryIssueList, SummaryTodoList } from "@/components/meeting/summary-lists";
import { PageSkeleton } from "@/components/page-skeleton";
import { SectionCard } from "@/components/section-card";
import { useTeamContext } from "@/components/team/team-context";
import { SCORE_STATUS } from "@/components/team/status";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { MeetingSummary } from "@/lib/api/client";
import { errorMessage } from "@/lib/api/errors";
import { useMeetingSummary } from "@/lib/api/meetings";
import { formatDate, formatDateTime, formatDuration, formatGoal, formatRating, formatValue } from "@/lib/format";
import { teamPath } from "@/lib/routes";
import { cn } from "@/lib/utils";

export function MeetingSummaryView({ meetingId }: { meetingId: string }) {
  const { teamId } = useTeamContext();
  const summary = useMeetingSummary(teamId, meetingId, "final");

  if (summary.isPending) {
    return <PageSkeleton />;
  }
  if (summary.isError) {
    return <ErrorState message={errorMessage(summary.error)} onRetry={() => void summary.refetch()} />;
  }
  return (
    <div className="flex flex-col gap-6">
      <SummaryHeader summary={summary.data} />
      <SectionCard title="Scorecard" description={`Week of ${formatDate(summary.data.scorecard_week)}`}>
        <ScorecardStatuses summary={summary.data} />
      </SectionCard>
      <div className="grid items-start gap-6 lg:grid-cols-2">
        <SectionCard title={`Issues solved (${summary.data.issues_solved.length})`}>
          <SummaryIssueList issues={summary.data.issues_solved} empty="No Issues were solved in this meeting." />
        </SectionCard>
        <SectionCard title={`To-Dos created (${summary.data.todos_created.length})`}>
          <SummaryTodoList todos={summary.data.todos_created} empty="No To-Dos were added in this meeting." />
        </SectionCard>
      </div>
    </div>
  );
}

function SummaryHeader({ summary }: { summary: MeetingSummary }) {
  const { teamId, teamName, timezone } = useTeamContext();
  const ratingOf = (userId: string) => summary.ratings.find((entry) => entry.user.id === userId)?.rating;

  return (
    <div className="flex flex-wrap items-start justify-between gap-6 rounded-lg border bg-card p-6 shadow-sm">
      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold">Meeting summary</h1>
          <p className="text-sm text-muted-foreground">
            {teamName} · {formatDateTime(summary.started_at, timezone)}
            {summary.ended_at && ` · ${formatDuration(summary.started_at, summary.ended_at)}`}
          </p>
        </div>
        <ul aria-label="Attendees" className="flex flex-wrap gap-1.5">
          {summary.attendees.map((attendee) => {
            const rating = ratingOf(attendee.id);
            return (
              <li key={attendee.id}>
                <Badge variant="secondary">
                  {attendee.name}
                  {rating !== undefined && ` · ${rating}`}
                </Badge>
              </li>
            );
          })}
        </ul>
        <Button asChild variant="outline" className="self-start">
          <Link href={teamPath(teamId)}>Back to the team</Link>
        </Button>
      </div>
      <p className="text-right">
        <span className="block text-5xl font-semibold tabular-nums">
          {summary.rating === null ? "–" : formatRating(summary.rating)}
        </span>
        <span className="text-sm text-muted-foreground">
          {summary.rating === null ? "Nobody rated this meeting" : `Rating from ${summary.ratings.length}`}
        </span>
      </p>
    </div>
  );
}

function ScorecardStatuses({ summary }: { summary: MeetingSummary }) {
  if (summary.measurables.length === 0) {
    return <p className="text-sm text-muted-foreground">This team has no Measurables.</p>;
  }
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left text-muted-foreground">
          <th className="py-2 font-medium">Measurable</th>
          <th className="py-2 font-medium">Goal</th>
          <th className="py-2 font-medium">Score</th>
          <th className="py-2 font-medium">Status</th>
        </tr>
      </thead>
      <tbody className="divide-y">
        {summary.measurables.map((measurable) => {
          const status = SCORE_STATUS[measurable.status];
          return (
            <tr key={measurable.id}>
              <td className="py-2">
                <span className="block">{measurable.name}</span>
                <span className="text-xs text-muted-foreground">{measurable.owner.name}</span>
              </td>
              <td className="py-2 text-muted-foreground">{formatGoal(measurable.goal, measurable.unit)}</td>
              <td className="py-2 tabular-nums">
                {measurable.value === null ? "–" : formatValue(measurable.value, measurable.unit)}
              </td>
              <td className="py-2">
                <span className={cn("rounded-md px-2 py-0.5 text-xs font-medium", status.cell)}>{status.label}</span>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
