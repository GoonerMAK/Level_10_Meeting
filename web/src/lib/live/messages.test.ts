import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";

import type { MeetingState } from "../api/client";
import { queryKeys } from "../api/query-keys";
import { applyLiveMessage, parseLiveMessage } from "./messages";

const meeting: MeetingState = {
  id: "meeting-1",
  team_id: "team-1",
  facilitator: { id: "user-1", name: "Ada" },
  attendees: [{ id: "user-1", name: "Ada" }],
  ratings: [],
  started_at: "2026-11-11T15:00:00Z",
  ended_at: null,
  section: "ids",
  section_started_at: "2026-11-11T15:05:00Z",
  section_ends_at: "2026-11-11T16:05:00Z",
  over_time: false,
  server_now: "2026-11-11T15:10:00Z",
};

describe("parseLiveMessage", () => {
  it("accepts the messages the server sends", () => {
    expect(parseLiveMessage(JSON.stringify({ type: "changed", what: "issues" }))).toEqual({
      type: "changed",
      what: "issues",
    });
    expect(parseLiveMessage(JSON.stringify({ type: "meeting", meeting }))).toEqual({ type: "meeting", meeting });
    expect(parseLiveMessage(JSON.stringify({ type: "meeting", meeting: null }))).toEqual({
      type: "meeting",
      meeting: null,
    });
  });

  it("drops anything it does not recognise", () => {
    expect(parseLiveMessage("not json")).toBeNull();
    expect(parseLiveMessage(JSON.stringify({ type: "changed", what: "rocks" }))).toBeNull();
    expect(parseLiveMessage(JSON.stringify({ type: "meeting", meeting: { id: "meeting-1" } }))).toBeNull();
  });
});

describe("applyLiveMessage", () => {
  it("refetches only the team data that changed", async () => {
    const queryClient = new QueryClient();
    queryClient.setQueryData(queryKeys.teamData("team-1", "issues"), []);
    queryClient.setQueryData(queryKeys.teamData("team-1", "todos"), []);
    queryClient.setQueryData(queryKeys.teamData("team-2", "issues"), []);

    await applyLiveMessage({ queryClient, teamId: "team-1", message: { type: "changed", what: "issues" } });

    const isInvalidated = (key: readonly string[]) => queryClient.getQueryState(key)?.isInvalidated;
    expect(isInvalidated(queryKeys.teamData("team-1", "issues"))).toBe(true);
    expect(isInvalidated(queryKeys.teamData("team-1", "todos"))).toBe(false);
    expect(isInvalidated(queryKeys.teamData("team-2", "issues"))).toBe(false);
  });

  it("stores the pushed meeting state, including when the meeting ends", async () => {
    const queryClient = new QueryClient();

    await applyLiveMessage({ queryClient, teamId: "team-1", message: { type: "meeting", meeting } });
    expect(queryClient.getQueryData(queryKeys.activeMeeting("team-1"))).toEqual(meeting);

    await applyLiveMessage({ queryClient, teamId: "team-1", message: { type: "meeting", meeting: null } });
    expect(queryClient.getQueryData(queryKeys.activeMeeting("team-1"))).toBeNull();
  });
});
