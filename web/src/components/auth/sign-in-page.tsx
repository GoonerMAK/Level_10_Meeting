"use client";

import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";

import { ErrorState } from "@/components/error-state";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useSignIn, useSignInChoices } from "@/lib/api/auth";
import type { UserChoice } from "@/lib/api/client";
import { errorMessage } from "@/lib/api/errors";
import { ROLE_LABELS } from "@/lib/permissions";

export function SignInPage() {
  const choices = useSignInChoices();
  const signIn = useSignIn();
  const router = useRouter();

  const choose = (userId: string) => signIn.mutate(userId, { onSuccess: () => router.replace("/") });

  return (
    <main className="flex flex-1 items-center justify-center bg-muted/40 p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-xl">Sign in</CardTitle>
          <CardDescription>Choose a seeded user to continue.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {choices.isPending && <ChoicesSkeleton />}
          {choices.isError && (
            <ErrorState message={errorMessage(choices.error)} onRetry={() => void choices.refetch()} />
          )}
          {choices.data && (
            <ul className="flex flex-col divide-y rounded-lg border">
              {choices.data.map((user) => (
                <li key={user.id}>
                  <UserChoiceButton
                    user={user}
                    disabled={signIn.isPending}
                    loading={signIn.isPending && signIn.variables === user.id}
                    onChoose={choose}
                  />
                </li>
              ))}
            </ul>
          )}
          {signIn.isError && <ErrorState message={errorMessage(signIn.error)} />}
        </CardContent>
      </Card>
    </main>
  );
}

type UserChoiceButtonProps = {
  user: UserChoice;
  disabled: boolean;
  loading: boolean;
  onChoose: (userId: string) => void;
};

function UserChoiceButton({ user, disabled, loading, onChoose }: UserChoiceButtonProps) {
  const teamNames = user.teams.map((team) => team.name).join(", ");
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => onChoose(user.id)}
      className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left transition-colors hover:bg-muted focus-visible:bg-muted focus-visible:outline-none disabled:opacity-60"
    >
      <span className="flex min-w-0 flex-col">
        <span className="text-sm font-medium">{user.name}</span>
        <span className="truncate text-xs text-muted-foreground">{teamNames || "No teams"}</span>
      </span>
      {loading ? (
        <Loader2 aria-label="Signing in" className="size-4 animate-spin text-muted-foreground" />
      ) : (
        <Badge variant={user.role === "observer" ? "outline" : "secondary"}>{ROLE_LABELS[user.role]}</Badge>
      )}
    </button>
  );
}

function ChoicesSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading users" className="flex flex-col gap-2">
      {Array.from({ length: 5 }, (_, index) => (
        <Skeleton key={index} className="h-12 w-full" />
      ))}
    </div>
  );
}
