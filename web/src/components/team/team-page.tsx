"use client";

import { useParams } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { useTeam } from "@/lib/api/teams";
import { ROLE_LABELS } from "@/lib/permissions";

export function TeamPage() {
  const { teamId } = useParams<{ teamId: string }>();
  const team = useTeam(teamId);
  if (!team.data) {
    return null;
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-baseline gap-x-4 gap-y-2">
        <h1 className="text-2xl font-semibold">{team.data.name}</h1>
        <ul aria-label="Team members" className="flex flex-wrap gap-1.5">
          {team.data.members.map((member) => (
            <li key={member.id}>
              <Badge variant="outline" className="font-normal">
                {member.name} · {ROLE_LABELS[member.role]}
              </Badge>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
