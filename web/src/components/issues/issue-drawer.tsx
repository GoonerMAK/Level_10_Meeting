"use client";

import { CheckCircle2, Circle } from "lucide-react";

import { AddTodoForm } from "@/components/issues/add-todo-form";
import { PriorityBadge } from "@/components/issues/priority-badge";
import { PrioritySelect } from "@/components/issues/priority-select";
import { SolveIssueForm } from "@/components/issues/solve-issue-form";
import { useSelectedIssue } from "@/components/team/issue-param";
import { useTeamContext } from "@/components/team/team-context";
import { Badge } from "@/components/ui/badge";
import { FieldError, FieldLabel } from "@/components/ui/field";
import { Separator } from "@/components/ui/separator";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import type { Issue } from "@/lib/api/client";
import { errorMessage } from "@/lib/api/errors";
import { useIssues, useSetPriority } from "@/lib/api/issues";
import { useTodos } from "@/lib/api/todos";
import { formatDate, formatDateTime } from "@/lib/format";
import { toPriority, toPriorityChoice } from "@/lib/validation";

export function IssueDrawer() {
  const { teamId } = useTeamContext();
  const { issueId, closeIssue } = useSelectedIssue();
  const openIssues = useIssues(teamId, "open");
  const openMatch = openIssues.data?.find((issue) => issue.id === issueId);
  const solvedIssues = useIssues(teamId, "solved", {
    enabled: issueId !== null && openIssues.isSuccess && !openMatch,
  });
  const issue = openMatch ?? solvedIssues.data?.find((candidate) => candidate.id === issueId);
  const loading = openIssues.isPending || (!openMatch && solvedIssues.isPending);

  return (
    <Sheet open={issueId !== null} onOpenChange={(open) => !open && closeIssue()}>
      <SheetContent className="w-full gap-0 overflow-y-auto sm:max-w-lg">
        {issue ? (
          <IssueDetails issue={issue} />
        ) : (
          <SheetHeader>
            <SheetTitle>Issue</SheetTitle>
            {loading ? (
              <Skeleton aria-label="Loading Issue" className="h-24 w-full" />
            ) : (
              <SheetDescription>This Issue isn&apos;t on this team.</SheetDescription>
            )}
          </SheetHeader>
        )}
      </SheetContent>
    </Sheet>
  );
}

function IssueDetails({ issue }: { issue: Issue }) {
  const { teamId, timezone, canChange } = useTeamContext();
  const solved = issue.solved_at !== null;

  return (
    <>
      <SheetHeader className="pr-12">
        <div className="flex items-center gap-2">
          <Badge variant={solved ? "secondary" : "outline"}>{solved ? "Solved" : "Open"}</Badge>
          {(!canChange || solved) && <PriorityBadge priority={issue.priority} />}
        </div>
        <SheetTitle className="text-lg">{issue.title}</SheetTitle>
        <SheetDescription>
          {issue.owner.name} · created {formatDateTime(issue.created_at, timezone)}
          {issue.source && (
            <span className="block">
              From Scorecard: {issue.source.measurable_name}, week of {formatDate(issue.source.week_start)}
            </span>
          )}
        </SheetDescription>
      </SheetHeader>

      <div className="flex flex-col gap-6 px-4 pb-6">
        {canChange && !solved && <PriorityControl teamId={teamId} issue={issue} />}

        {issue.solved_at && (
          <div className="flex flex-col gap-1 rounded-lg bg-muted/50 p-3">
            <span className="text-xs text-muted-foreground">Solved {formatDateTime(issue.solved_at, timezone)}</span>
            <p className="whitespace-pre-wrap">{issue.resolution_note}</p>
          </div>
        )}

        <Separator />
        <IssueTodos issue={issue} />
        {canChange && <AddTodoForm issue={issue} />}

        {canChange && !solved && (
          <>
            <Separator />
            <SolveIssueForm issue={issue} />
          </>
        )}
      </div>
    </>
  );
}

function PriorityControl({ teamId, issue }: { teamId: string; issue: Issue }) {
  const setPriority = useSetPriority(teamId);
  const selectId = `priority-${issue.id}`;

  return (
    <div className="flex flex-col gap-2">
      <FieldLabel htmlFor={selectId}>Priority</FieldLabel>
      <PrioritySelect
        id={selectId}
        value={toPriorityChoice(issue.priority)}
        disabled={setPriority.isPending}
        invalid={setPriority.isError ? true : undefined}
        onChange={(choice) => setPriority.mutate({ issueId: issue.id, priority: toPriority(choice) })}
      />
      {setPriority.isError && <FieldError>{errorMessage(setPriority.error)}</FieldError>}
    </div>
  );
}

function IssueTodos({ issue }: { issue: Issue }) {
  const { teamId } = useTeamContext();
  const todos = useTodos(teamId);
  const fromIssue = todos.data?.todos.filter((todo) => todo.source_issue?.id === issue.id) ?? [];

  return (
    <div className="flex flex-col gap-2">
      <h3 className="font-medium">To-Dos from this Issue</h3>
      {fromIssue.length === 0 ? (
        <p className="text-xs text-muted-foreground">None yet.</p>
      ) : (
        <ul className="flex flex-col gap-1.5">
          {fromIssue.map((todo) => (
            <li key={todo.id} className="flex items-start gap-2">
              {todo.done_at ? (
                <CheckCircle2 aria-label="Done" className="mt-0.5 size-4 shrink-0 text-emerald-600" />
              ) : (
                <Circle aria-label="Not done" className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
              )}
              <span className="flex flex-col">
                <span>{todo.title}</span>
                <span className="text-xs text-muted-foreground">
                  {todo.owner.name} · due {formatDate(todo.due_date)}
                </span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
