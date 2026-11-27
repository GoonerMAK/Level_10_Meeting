import type { QueryClient } from "@tanstack/react-query";

import type { MeetingState } from "../api/client";
import { queryKeys, type TeamData } from "../api/query-keys";

export type LiveMessage =
  | { type: "hello" }
  | { type: "changed"; what: TeamData }
  | { type: "meeting"; meeting: MeetingState | null };

const TEAM_DATA: readonly TeamData[] = ["scorecard", "issues", "todos"];
const SECTIONS: readonly unknown[] = ["scorecard", "ids", "conclude", null];

const isRecord = (value: unknown): value is Record<string, unknown> => typeof value === "object" && value !== null;

const isTeamData = (value: unknown): value is TeamData => TEAM_DATA.some((what) => what === value);

const isUserRef = (value: unknown): boolean =>
  isRecord(value) && typeof value.id === "string" && typeof value.name === "string";

export const isMeetingState = (value: unknown): value is MeetingState =>
  isRecord(value) &&
  typeof value.id === "string" &&
  typeof value.team_id === "string" &&
  isUserRef(value.facilitator) &&
  Array.isArray(value.attendees) &&
  value.attendees.every(isUserRef) &&
  Array.isArray(value.ratings) &&
  typeof value.started_at === "string" &&
  (value.ended_at === null || typeof value.ended_at === "string") &&
  SECTIONS.includes(value.section) &&
  typeof value.over_time === "boolean" &&
  typeof value.server_now === "string";

export function parseLiveMessage(raw: string): LiveMessage | null {
  let message: unknown;
  try {
    message = JSON.parse(raw);
  } catch {
    return null;
  }
  if (!isRecord(message)) {
    return null;
  }
  if (message.type === "hello") {
    return { type: "hello" };
  }
  if (message.type === "changed" && isTeamData(message.what)) {
    return { type: "changed", what: message.what };
  }
  if (message.type === "meeting" && (message.meeting === null || isMeetingState(message.meeting))) {
    return { type: "meeting", meeting: message.meeting };
  }
  return null;
}

export async function applyLiveMessage({
  queryClient,
  teamId,
  message,
}: {
  queryClient: QueryClient;
  teamId: string;
  message: LiveMessage;
}): Promise<void> {
  switch (message.type) {
    case "hello":
      return;
    case "changed":
      await queryClient.invalidateQueries({ queryKey: queryKeys.teamData(teamId, message.what) });
      return;
    case "meeting":
      queryClient.setQueryData(queryKeys.activeMeeting(teamId), message.meeting);
      return;
    default: {
      const exhaustive: never = message;
      return exhaustive;
    }
  }
}
