"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Plus } from "lucide-react";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { PrioritySelect } from "@/components/issues/priority-select";
import { useTeamContext } from "@/components/team/team-context";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { useCreateIssue } from "@/lib/api/issues";
import { showServerErrors } from "@/lib/forms";
import { NO_PRIORITY, priorityChoiceSchema, titleSchema, toPriority } from "@/lib/validation";

const newIssueSchema = z.object({ title: titleSchema, priority: priorityChoiceSchema });
type NewIssueForm = z.infer<typeof newIssueSchema>;

export function NewIssueDialog() {
  const { teamId } = useTeamContext();
  const [open, setOpen] = useState(false);
  const createIssue = useCreateIssue(teamId);
  const form = useForm<NewIssueForm>({
    resolver: zodResolver(newIssueSchema),
    defaultValues: { title: "", priority: NO_PRIORITY },
  });
  const { errors } = form.formState;

  const handleOpenChange = (nextOpen: boolean) => {
    setOpen(nextOpen);
    if (!nextOpen) {
      form.reset();
    }
  };

  const submit = form.handleSubmit(({ title, priority }) =>
    createIssue.mutate(
      { title, priority: toPriority(priority) },
      {
        onSuccess: (issue) => {
          handleOpenChange(false);
          toast.success("Issue added", { description: issue.title });
        },
        onError: (error) => showServerErrors(form, error, { title: "title", priority: "priority" }),
      },
    ),
  );

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus />
          New Issue
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={submit} noValidate className="flex flex-col gap-6">
          <DialogHeader>
            <DialogTitle>New Issue</DialogTitle>
            <DialogDescription>You&apos;ll own it. The team works it in the meeting&apos;s IDS.</DialogDescription>
          </DialogHeader>
          <FieldGroup>
            <Field data-invalid={errors.title ? true : undefined}>
              <FieldLabel htmlFor="new-issue-title">Title</FieldLabel>
              <Input
                id="new-issue-title"
                autoFocus
                aria-invalid={errors.title ? true : undefined}
                {...form.register("title")}
              />
              <FieldError errors={[errors.title]} />
            </Field>
            <Field data-invalid={errors.priority ? true : undefined}>
              <FieldLabel htmlFor="new-issue-priority">Priority</FieldLabel>
              <Controller
                control={form.control}
                name="priority"
                render={({ field }) => (
                  <PrioritySelect
                    id="new-issue-priority"
                    value={field.value}
                    onChange={field.onChange}
                    invalid={errors.priority ? true : undefined}
                  />
                )}
              />
              <FieldError errors={[errors.priority]} />
            </Field>
            <FieldError errors={[errors.root?.server]} />
          </FieldGroup>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => handleOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={createIssue.isPending}>
              Add Issue
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
