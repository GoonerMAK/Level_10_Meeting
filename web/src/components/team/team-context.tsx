"use client";

import { createContext, use, useMemo, type ReactNode } from "react";

import { useCurrentUser } from "@/components/auth/require-sign-in";
import type { TeamDetail, TodoOwner } from "@/lib/api/client";
import { canChangeTeam } from "@/lib/permissions";

type TeamContextValue = {
  teamId: string;
  teamName: string;
  timezone: string;
  canChange: boolean;
  todoOwners: TodoOwner[];
};

const TeamContext = createContext<TeamContextValue | null>(null);

export function TeamProvider({ team, children }: { team: TeamDetail; children: ReactNode }) {
  const me = useCurrentUser();
  const value = useMemo(
    () => ({
      teamId: team.id,
      teamName: team.name,
      timezone: team.timezone,
      canChange: canChangeTeam(me, team.id),
      todoOwners: team.todo_owners,
    }),
    [me, team],
  );
  return <TeamContext value={value}>{children}</TeamContext>;
}

export function useTeamContext(): TeamContextValue {
  const team = use(TeamContext);
  if (!team) {
    throw new Error("useTeamContext must be used inside TeamProvider");
  }
  return team;
}
