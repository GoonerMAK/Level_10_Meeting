import type { Me, UserRole } from "./api/client";

export const ROLE_LABELS: Record<UserRole, string> = {
  admin: "Admin",
  team_member: "Team Member",
  observer: "Observer",
};

export const canChangeTeam = (me: Pick<Me, "role" | "team_ids">, teamId: string): boolean =>
  me.role === "admin" || (me.role === "team_member" && me.team_ids.includes(teamId));
