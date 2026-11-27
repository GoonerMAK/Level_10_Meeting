import type { Schemas } from "@/lib/api/client";

type ScoreStatus = Schemas["ScoreCell"]["status"];
type RockStatus = Schemas["RockStatus"];

export const SCORE_STATUS: Record<ScoreStatus, { label: string; cell: string }> = {
  on_track: { label: "On track", cell: "bg-emerald-50 text-emerald-950" },
  off_track: { label: "Off track", cell: "bg-red-50 text-red-950" },
  pending: { label: "Pending", cell: "bg-muted/50 text-muted-foreground" },
};

export const ROCK_STATUS: Record<RockStatus, { label: string; badge: string }> = {
  on_track: { label: "On track", badge: "border-transparent bg-emerald-100 text-emerald-900" },
  off_track: { label: "Off track", badge: "border-transparent bg-red-100 text-red-900" },
  complete: { label: "Complete", badge: "border-transparent bg-secondary text-secondary-foreground" },
};
