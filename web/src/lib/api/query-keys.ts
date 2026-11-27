export type TeamData = "scorecard" | "issues" | "todos";
export type IssueStatus = "open" | "solved";

export const queryKeys = {
  me: ["me"] as const,
  signInChoices: ["sign-in-choices"] as const,
  teams: ["teams"] as const,
  team: (teamId: string) => ["team", teamId] as const,
  teamDetail: (teamId: string) => ["team", teamId, "detail"] as const,
  teamData: (teamId: string, what: TeamData) => ["team", teamId, what] as const,
  issues: (teamId: string, status: IssueStatus) => ["team", teamId, "issues", status] as const,
  rocks: (teamId: string) => ["team", teamId, "rocks"] as const,
  activeMeeting: (teamId: string) => ["team", teamId, "meeting"] as const,
  serverClockOffset: ["server-clock-offset"] as const,
};
