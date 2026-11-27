"use client";

import { ErrorState } from "@/components/error-state";
import { NewIssueDialog } from "@/components/issues/new-issue-dialog";
import { PriorityBadge } from "@/components/issues/priority-badge";
import { SectionCard } from "@/components/section-card";
import { useOpenIssue, useSelectedIssue } from "@/components/team/issue-param";
import { useTeamContext } from "@/components/team/team-context";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Issue } from "@/lib/api/client";
import { errorMessage } from "@/lib/api/errors";
import { useIssues } from "@/lib/api/issues";
import type { IssueStatus } from "@/lib/api/query-keys";
import { formatDate, formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";

export function IssuesSection() {
  const { canChange } = useTeamContext();

  return (
    <SectionCard title="Issues" description="Highest priority first, then oldest" actions={canChange && <NewIssueDialog />}>
      <Tabs defaultValue="open">
        <TabsList>
          <TabsTrigger value="open">Open</TabsTrigger>
          <TabsTrigger value="solved">Solved</TabsTrigger>
        </TabsList>
        <TabsContent value="open">
          <IssueList status="open" />
        </TabsContent>
        <TabsContent value="solved">
          <IssueList status="solved" />
        </TabsContent>
      </Tabs>
    </SectionCard>
  );
}

const EMPTY_MESSAGES: Record<IssueStatus, string> = {
  open: "No open Issues. Add one, or flag an off-track score on the Scorecard.",
  solved: "No solved Issues yet.",
};

function IssueList({ status }: { status: IssueStatus }) {
  const { teamId } = useTeamContext();
  const issues = useIssues(teamId, status);
  const openIssue = useOpenIssue();
  const { issueId } = useSelectedIssue();

  if (issues.isPending) {
    return <Skeleton aria-label="Loading Issues" className="h-32 w-full" />;
  }
  if (issues.isError) {
    return <ErrorState message={errorMessage(issues.error)} onRetry={() => void issues.refetch()} />;
  }
  if (issues.data.length === 0) {
    return <p className="py-4 text-sm text-muted-foreground">{EMPTY_MESSAGES[status]}</p>;
  }
  return (
    <ul className="flex flex-col divide-y rounded-lg border">
      {issues.data.map((issue) => (
        <li key={issue.id}>
          <IssueRow issue={issue} selected={issue.id === issueId} onOpen={() => openIssue(issue.id)} />
        </li>
      ))}
    </ul>
  );
}

function IssueRow({ issue, selected, onOpen }: { issue: Issue; selected: boolean; onOpen: () => void }) {
  const { timezone } = useTeamContext();

  return (
    <button
      type="button"
      onClick={onOpen}
      aria-current={selected ? "true" : undefined}
      className={cn(
        "grid w-full grid-cols-[auto_1fr_auto] items-center gap-3 px-3 py-2.5 text-left transition-colors hover:bg-muted focus-visible:bg-muted focus-visible:outline-none",
        selected && "bg-muted",
      )}
    >
      <PriorityBadge priority={issue.priority} />
      <span className="flex min-w-0 flex-col">
        <span className="truncate font-medium">{issue.title}</span>
        <span className="truncate text-xs text-muted-foreground">
          {issue.solved_at
            ? `Solved ${formatDateTime(issue.solved_at, timezone)} · ${issue.resolution_note ?? ""}`
            : issue.source
              ? `From Scorecard: ${issue.source.measurable_name}, week of ${formatDate(issue.source.week_start)}`
              : "Added directly"}
        </span>
      </span>
      <span className="flex flex-col items-end text-xs text-muted-foreground">
        <span className="text-foreground">{issue.owner.name}</span>
        <span>{formatDateTime(issue.created_at, timezone)}</span>
      </span>
    </button>
  );
}
