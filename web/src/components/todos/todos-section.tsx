"use client";

import { CheckCircle2, Circle } from "lucide-react";
import { toast } from "sonner";

import { ErrorState } from "@/components/error-state";
import { SectionCard } from "@/components/section-card";
import { useOpenIssue } from "@/components/team/issue-param";
import { useTeamContext } from "@/components/team/team-context";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import type { Completion, Todo } from "@/lib/api/client";
import { errorMessage } from "@/lib/api/errors";
import { useSetTodoDone, useTodos } from "@/lib/api/todos";
import { formatDate, formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";

export function TodosSection() {
  const { teamId } = useTeamContext();
  const todos = useTodos(teamId);

  const renderBody = () => {
    if (todos.isPending) {
      return <Skeleton aria-label="Loading To-Dos" className="h-32 w-full" />;
    }
    if (todos.isError) {
      return <ErrorState message={errorMessage(todos.error)} onRetry={() => void todos.refetch()} />;
    }
    if (todos.data.todos.length === 0) {
      return <p className="text-sm text-muted-foreground">No To-Dos. Add them from an Issue.</p>;
    }
    return (
      <ul className="flex flex-col divide-y">
        {todos.data.todos.map((todo) => (
          <li key={todo.id}>
            <TodoRow todo={todo} />
          </li>
        ))}
      </ul>
    );
  };

  return (
    <SectionCard
      title="To-Dos"
      description={todos.data && `Completion counts To-Dos due the week of ${formatDate(todos.data.completion_week)}`}
      actions={todos.data && <CompletionBadge completion={todos.data.completion} />}
    >
      {renderBody()}
    </SectionCard>
  );
}

function CompletionBadge({ completion }: { completion: Completion | null }) {
  if (!completion) {
    return <span className="text-xs text-muted-foreground">Nothing was due last week</span>;
  }
  return (
    <Badge
      variant="outline"
      title="Target 90%"
      className={cn(
        "border-transparent",
        completion.meets_target ? "bg-emerald-100 text-emerald-900" : "bg-red-100 text-red-900",
      )}
    >
      Last week {completion.rate_percent}% · {completion.done}/{completion.due} done
      <span className="sr-only">{completion.meets_target ? ", meets the 90% target" : ", below the 90% target"}</span>
    </Badge>
  );
}

function TodoRow({ todo }: { todo: Todo }) {
  const { teamId, timezone, canChange } = useTeamContext();
  const setDone = useSetTodoDone(teamId);
  const openIssue = useOpenIssue();
  const done = todo.done_at !== null;
  const sourceIssue = todo.source_issue;
  const checkboxId = `todo-${todo.id}`;

  const toggle = (checked: boolean) =>
    setDone.mutate({ todoId: todo.id, done: checked }, { onError: (error) => toast.error(errorMessage(error)) });

  return (
    <div className="flex items-start gap-3 py-2.5">
      {canChange ? (
        <Checkbox
          id={checkboxId}
          checked={done}
          disabled={setDone.isPending}
          onCheckedChange={(checked) => toggle(checked === true)}
          className="mt-0.5"
        />
      ) : done ? (
        <CheckCircle2 aria-label="Done" className="mt-0.5 size-4 shrink-0 text-emerald-600" />
      ) : (
        <Circle aria-label="Not done" className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
      )}
      <div className="flex min-w-0 flex-col gap-0.5">
        <label htmlFor={canChange ? checkboxId : undefined} className={cn(done && "text-muted-foreground line-through")}>
          {todo.title}
        </label>
        <span className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
          <span>{todo.owner.name}</span>
          <span>Due {formatDate(todo.due_date)}</span>
          {todo.overdue && (
            <Badge variant="outline" className="border-transparent bg-red-100 text-red-900">
              Overdue
            </Badge>
          )}
          {todo.done_at && <span>Done {formatDateTime(todo.done_at, timezone)}</span>}
          {sourceIssue && (
            <button
              type="button"
              onClick={() => openIssue(sourceIssue.id)}
              className="max-w-56 truncate underline-offset-2 hover:text-foreground hover:underline"
            >
              From Issue: {sourceIssue.title}
            </button>
          )}
        </span>
      </div>
    </div>
  );
}
