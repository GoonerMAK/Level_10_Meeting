"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Flag } from "lucide-react";
import { useRef, useState, type KeyboardEvent } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { useOpenIssue } from "@/components/team/issue-param";
import { SCORE_STATUS } from "@/components/team/status";
import { useTeamContext } from "@/components/team/team-context";
import { Input } from "@/components/ui/input";
import type { MeasurableRow, ScoreCell } from "@/lib/api/client";
import { errorMessage } from "@/lib/api/errors";
import { useMakeIssue, useUpdateScore } from "@/lib/api/scorecard";
import { formatDate, formatNumber, formatValue } from "@/lib/format";
import { showServerErrors } from "@/lib/forms";
import { cn } from "@/lib/utils";
import { scoreValueSchema } from "@/lib/validation";

type ScoreCellProps = { measurable: MeasurableRow; cell: ScoreCell };

export function ScoreCellView({ measurable, cell }: ScoreCellProps) {
  const { canChange } = useTeamContext();
  const [editing, setEditing] = useState(false);
  const status = SCORE_STATUS[cell.status];
  const value = cell.value === null ? "no score" : formatValue(cell.value, measurable.unit);
  const label = `${measurable.name}, week of ${formatDate(cell.week_start)}: ${value}, ${status.label}`;

  if (editing) {
    return <ScoreInput measurable={measurable} cell={cell} onDone={() => setEditing(false)} />;
  }

  return (
    <div className={cn("group relative flex h-9 items-center justify-center rounded-md tabular-nums", status.cell)}>
      {canChange ? (
        <button
          type="button"
          aria-label={`${label}. Edit score`}
          onClick={() => setEditing(true)}
          className="size-full rounded-md outline-none hover:ring-1 hover:ring-ring focus-visible:ring-2 focus-visible:ring-ring"
        >
          {cell.value === null ? "" : formatNumber(cell.value)}
        </button>
      ) : (
        <span aria-label={label}>{cell.value === null ? "" : formatNumber(cell.value)}</span>
      )}
      {canChange && cell.status === "off_track" && <MakeIssueButton measurable={measurable} cell={cell} />}
    </div>
  );
}

function MakeIssueButton({ measurable, cell }: ScoreCellProps) {
  const { teamId } = useTeamContext();
  const makeIssue = useMakeIssue(teamId);
  const openIssue = useOpenIssue();

  const handleClick = () =>
    makeIssue.mutate(
      { measurableId: measurable.id, weekStart: cell.week_start },
      {
        onSuccess: ({ issue, created }) =>
          toast.success(created ? "Issue created" : "This score already has an open Issue", {
            description: issue.title,
            action: { label: "Open", onClick: () => openIssue(issue.id) },
          }),
        onError: (error) => toast.error(errorMessage(error)),
      },
    );

  return (
    <button
      type="button"
      aria-label={`Make it an Issue: ${measurable.name}, week of ${formatDate(cell.week_start)}`}
      title="Make it an Issue"
      disabled={makeIssue.isPending}
      onClick={handleClick}
      className="absolute top-0.5 right-0.5 rounded-sm p-0.5 text-red-700 opacity-0 transition-opacity group-hover:opacity-100 hover:bg-red-100 focus-visible:opacity-100 focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
    >
      <Flag className="size-3" />
    </button>
  );
}

const scoreFormSchema = z.object({ value: scoreValueSchema });
type ScoreForm = z.infer<typeof scoreFormSchema>;

function ScoreInput({ measurable, cell, onDone }: ScoreCellProps & { onDone: () => void }) {
  const { teamId } = useTeamContext();
  const updateScore = useUpdateScore(teamId);
  const form = useForm<ScoreForm>({
    resolver: zodResolver(scoreFormSchema),
    defaultValues: { value: cell.value === null ? "" : String(cell.value) },
  });
  const field = form.register("value");
  const saving = useRef(false);
  const error = form.formState.errors.value?.message ?? form.formState.errors.root?.server?.message;

  const save = () => {
    if (saving.current) {
      return;
    }
    if (form.getValues("value").trim() === "") {
      onDone();
      return;
    }
    void form.handleSubmit(({ value }) => {
      if (Number(value) === cell.value) {
        onDone();
        return;
      }
      saving.current = true;
      updateScore.mutate(
        { measurableId: measurable.id, weekStart: cell.week_start, value },
        {
          onSuccess: onDone,
          onError: (serverError) => {
            saving.current = false;
            showServerErrors(form, serverError, { value: "value" });
          },
        },
      );
    })();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Escape") {
      event.preventDefault();
      onDone();
    }
  };

  return (
    <form
      className="relative"
      onSubmit={(event) => {
        event.preventDefault();
        save();
      }}
    >
      <Input
        {...field}
        autoFocus
        inputMode="decimal"
        aria-label={`Score for ${measurable.name}, week of ${formatDate(cell.week_start)}`}
        aria-invalid={error ? true : undefined}
        disabled={updateScore.isPending}
        onKeyDown={handleKeyDown}
        onBlur={(event) => {
          void field.onBlur(event);
          save();
        }}
        className="h-9 w-16 px-1 text-center tabular-nums"
      />
      {error && (
        <p
          role="alert"
          className="absolute top-full left-0 z-20 mt-1 w-48 rounded-md border bg-popover p-2 text-xs text-destructive shadow-md"
        >
          {error}
        </p>
      )}
    </form>
  );
}
