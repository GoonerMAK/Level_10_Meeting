import { useTeamContext } from "@/components/team/team-context";
import type { Schemas } from "@/lib/api/client";
import { formatDate, formatDateTime } from "@/lib/format";

type SummaryTodo = Schemas["SummaryTodo"];
type SummaryIssue = Schemas["SummaryIssue"];

export function SummaryTodoList({ todos, empty }: { todos: SummaryTodo[]; empty: string }) {
  if (todos.length === 0) {
    return <p className="text-sm text-muted-foreground">{empty}</p>;
  }
  return (
    <ul className="flex flex-col divide-y">
      {todos.map((todo) => (
        <li key={todo.id} className="flex flex-col gap-0.5 py-2.5">
          <span>{todo.title}</span>
          <span className="text-xs text-muted-foreground">
            {todo.owner.name} · Due {formatDate(todo.due_date)}
          </span>
        </li>
      ))}
    </ul>
  );
}

export function SummaryIssueList({ issues, empty }: { issues: SummaryIssue[]; empty: string }) {
  const { timezone } = useTeamContext();
  if (issues.length === 0) {
    return <p className="text-sm text-muted-foreground">{empty}</p>;
  }
  return (
    <ul className="flex flex-col divide-y">
      {issues.map((issue) => (
        <li key={issue.id} className="flex flex-col gap-0.5 py-2.5">
          <span>{issue.title}</span>
          <span className="text-xs text-muted-foreground">
            {issue.owner.name} · Solved {formatDateTime(issue.solved_at, timezone)}
          </span>
        </li>
      ))}
    </ul>
  );
}
