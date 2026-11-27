"use client";

import { ChevronsUpDown } from "lucide-react";
import { useRouter } from "next/navigation";

import { useCurrentUser } from "@/components/auth/require-sign-in";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useTeams } from "@/lib/api/teams";

export function TeamSwitcher({ teamId }: { teamId: string }) {
  const me = useCurrentUser();
  const teams = useTeams();
  const router = useRouter();
  const current = teams.data?.find((team) => team.id === teamId);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="min-w-40 justify-between" aria-label="Switch team">
          <span className="truncate">{current?.name ?? "Choose a team"}</span>
          <ChevronsUpDown className="text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="min-w-48">
        <DropdownMenuLabel>{me.role === "admin" ? "All teams" : "Your teams"}</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuRadioGroup value={teamId} onValueChange={(nextTeamId) => router.push(`/teams/${nextTeamId}`)}>
          {teams.data?.map((team) => (
            <DropdownMenuRadioItem key={team.id} value={team.id}>
              {team.name}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
