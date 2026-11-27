"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { ErrorState } from "@/components/error-state";
import { PageSkeleton } from "@/components/page-skeleton";
import { errorMessage } from "@/lib/api/errors";
import { useTeams } from "@/lib/api/teams";

export function FirstTeamRedirect() {
  const teams = useTeams();
  const router = useRouter();
  const firstTeamId = teams.data?.[0]?.id;

  useEffect(() => {
    if (firstTeamId) {
      router.replace(`/teams/${firstTeamId}`);
    }
  }, [firstTeamId, router]);

  if (teams.isError) {
    return <ErrorState className="p-6" message={errorMessage(teams.error)} onRetry={() => void teams.refetch()} />;
  }
  if (teams.data && teams.data.length === 0) {
    return <p className="p-6 text-sm text-muted-foreground">You aren&apos;t on any team yet.</p>;
  }
  return <PageSkeleton />;
}
