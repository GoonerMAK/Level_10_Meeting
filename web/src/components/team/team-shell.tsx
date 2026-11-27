"use client";

import { useParams } from "next/navigation";
import type { ReactNode } from "react";

import { RequireSignIn } from "@/components/auth/require-sign-in";
import { ErrorState } from "@/components/error-state";
import { AppHeader } from "@/components/header/app-header";
import { PageSkeleton } from "@/components/page-skeleton";
import { AccessError } from "@/components/team/access-error";
import { errorMessage, isApiError } from "@/lib/api/errors";
import { useTeam } from "@/lib/api/teams";
import { useLiveTeam } from "@/lib/live/use-live-team";

export function TeamShell({ children }: { children: ReactNode }) {
  const { teamId } = useParams<{ teamId: string }>();
  return (
    <RequireSignIn>
      <TeamFrame teamId={teamId}>{children}</TeamFrame>
    </RequireSignIn>
  );
}

function TeamFrame({ teamId, children }: { teamId: string; children: ReactNode }) {
  const team = useTeam(teamId);
  const liveStatus = useLiveTeam({ teamId, enabled: team.isSuccess });

  const renderContent = () => {
    if (team.isPending) {
      return <PageSkeleton />;
    }
    if (isApiError(team.error, 404) || isApiError(team.error, 403)) {
      return <AccessError message={team.error.message} />;
    }
    if (team.isError) {
      return <ErrorState message={errorMessage(team.error)} onRetry={() => void team.refetch()} />;
    }
    return children;
  };

  return (
    <div className="flex min-h-screen flex-col">
      <AppHeader teamId={teamId} teamLoaded={team.isSuccess} liveStatus={liveStatus} />
      <main className="mx-auto w-full max-w-screen-2xl flex-1 px-4 py-6 lg:px-6">{renderContent()}</main>
    </div>
  );
}
