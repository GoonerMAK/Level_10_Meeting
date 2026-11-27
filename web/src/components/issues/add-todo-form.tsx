"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { useCurrentUser } from "@/components/auth/require-sign-in";
import { useTeamContext } from "@/components/team/team-context";
import { Button } from "@/components/ui/button";
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Issue, TodoOwner } from "@/lib/api/client";
import { useAddTodo } from "@/lib/api/issues";
import { showServerErrors } from "@/lib/forms";
import { titleSchema } from "@/lib/validation";

const addTodoSchema = z.object({
  title: titleSchema,
  ownerId: z.string().min(1, "Choose an owner"),
});
type AddTodoForm = z.infer<typeof addTodoSchema>;

const OWNER_GROUPS: { label: string; onTeam: boolean }[] = [
  { label: "Team", onTeam: true },
  { label: "Admins from other teams", onTeam: false },
];

export function AddTodoForm({ issue }: { issue: Issue }) {
  const me = useCurrentUser();
  const { teamId, todoOwners } = useTeamContext();
  const addTodo = useAddTodo(teamId);
  const defaultOwner = todoOwners.some((owner) => owner.id === me.id) ? me.id : "";
  const form = useForm<AddTodoForm>({
    resolver: zodResolver(addTodoSchema),
    defaultValues: { title: "", ownerId: defaultOwner },
  });
  const { errors } = form.formState;
  const titleId = `todo-title-${issue.id}`;
  const ownerId = `todo-owner-${issue.id}`;

  const submit = form.handleSubmit((values) =>
    addTodo.mutate(
      { issueId: issue.id, title: values.title, ownerId: values.ownerId },
      {
        onSuccess: (todo) => {
          form.reset({ title: "", ownerId: values.ownerId });
          toast.success("To-Do added", { description: `${todo.title} · ${todo.owner.name}` });
        },
        onError: (error) => showServerErrors(form, error, { title: "title", owner_id: "ownerId" }),
      },
    ),
  );

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-3">
      <FieldGroup className="gap-3">
        <Field data-invalid={errors.title ? true : undefined}>
          <FieldLabel htmlFor={titleId}>Add a To-Do</FieldLabel>
          <FieldDescription>Due in 7 days and linked to this Issue.</FieldDescription>
          <Input id={titleId} aria-invalid={errors.title ? true : undefined} {...form.register("title")} />
          <FieldError errors={[errors.title]} />
        </Field>
        <Field data-invalid={errors.ownerId ? true : undefined}>
          <FieldLabel htmlFor={ownerId}>Owner</FieldLabel>
          <Controller
            control={form.control}
            name="ownerId"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger id={ownerId} aria-invalid={errors.ownerId ? true : undefined} className="w-full">
                  <SelectValue placeholder="Choose an owner" />
                </SelectTrigger>
                <SelectContent>
                  {OWNER_GROUPS.map((group) => (
                    <OwnerGroup key={group.label} label={group.label} owners={todoOwners.filter((owner) => owner.on_team === group.onTeam)} />
                  ))}
                </SelectContent>
              </Select>
            )}
          />
          <FieldError errors={[errors.ownerId]} />
          <FieldError errors={[errors.root?.server]} />
        </Field>
      </FieldGroup>
      <Button type="submit" variant="outline" className="self-start" disabled={addTodo.isPending}>
        Add To-Do
      </Button>
    </form>
  );
}

function OwnerGroup({ label, owners }: { label: string; owners: TodoOwner[] }) {
  if (owners.length === 0) {
    return null;
  }
  return (
    <SelectGroup>
      <SelectLabel>{label}</SelectLabel>
      {owners.map((owner) => (
        <SelectItem key={owner.id} value={owner.id}>
          {owner.name}
          {owner.role === "admin" && <span className="text-muted-foreground"> · Admin</span>}
        </SelectItem>
      ))}
    </SelectGroup>
  );
}
