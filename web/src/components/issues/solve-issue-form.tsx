"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { useTeamContext } from "@/components/team/team-context";
import { Button } from "@/components/ui/button";
import { Field, FieldDescription, FieldError, FieldLabel } from "@/components/ui/field";
import { Textarea } from "@/components/ui/textarea";
import type { Issue } from "@/lib/api/client";
import { useSolveIssue } from "@/lib/api/issues";
import { showServerErrors } from "@/lib/forms";
import { noteSchema } from "@/lib/validation";

const solveSchema = z.object({ note: noteSchema });
type SolveForm = z.infer<typeof solveSchema>;

export function SolveIssueForm({ issue }: { issue: Issue }) {
  const { teamId } = useTeamContext();
  const solveIssue = useSolveIssue(teamId);
  const form = useForm<SolveForm>({ resolver: zodResolver(solveSchema), defaultValues: { note: "" } });
  const { errors } = form.formState;
  const noteId = `solve-note-${issue.id}`;

  const submit = form.handleSubmit(({ note }) =>
    solveIssue.mutate(
      { issueId: issue.id, note },
      {
        onSuccess: () => toast.success("Issue solved", { description: issue.title }),
        onError: (error) => showServerErrors(form, error, { resolution_note: "note" }),
      },
    ),
  );

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-3">
      <Field data-invalid={errors.note ? true : undefined}>
        <FieldLabel htmlFor={noteId}>Solve this Issue</FieldLabel>
        <FieldDescription>Write down what the team decided.</FieldDescription>
        <Textarea id={noteId} rows={3} aria-invalid={errors.note ? true : undefined} {...form.register("note")} />
        <FieldError errors={[errors.note]} />
        <FieldError errors={[errors.root?.server]} />
      </Field>
      <Button type="submit" className="self-start" disabled={solveIssue.isPending}>
        Solve Issue
      </Button>
    </form>
  );
}
