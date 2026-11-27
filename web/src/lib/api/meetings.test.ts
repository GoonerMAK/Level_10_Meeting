import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";

import type { MeetingState } from "./client";
import { storeMeeting } from "./meetings";
import { queryKeys } from "./query-keys";

const meeting: MeetingState = {
  id: "meeting-1",
  team_id: "team-1",
  facilitator: { id: "user-1", name: "Ada" },
  attendees: [{ id: "user-1", name: "Ada" }],
  ratings: [],
  started_at: "2026-11-11T15:00:00Z",
  ended_at: null,
  section: "scorecard",
  section_started_at: "2026-11-11T15:00:00Z",
  section_ends_at: "2026-11-11T15:05:00Z",
  over_time: false,
  server_now: "2026-11-11T15:01:00Z",
};

const moved: MeetingState = {
  ...meeting,
  section: "ids",
  section_started_at: "2026-11-11T15:02:00Z",
  section_ends_at: "2026-11-11T16:02:00Z",
  server_now: "2026-11-11T15:02:00Z",
};

describe("storeMeeting", () => {
  it("keeps the newer snapshot when an older one arrives late", () => {
    const queryClient = new QueryClient();
    storeMeeting(queryClient, "team-1", moved);
    storeMeeting(queryClient, "team-1", meeting);
    expect(queryClient.getQueryData(queryKeys.activeMeeting("team-1"))).toEqual(moved);
  });

  it("replaces the meeting when a different one or none arrives", () => {
    const queryClient = new QueryClient();
    storeMeeting(queryClient, "team-1", moved);
    storeMeeting(queryClient, "team-1", null);
    expect(queryClient.getQueryData(queryKeys.activeMeeting("team-1"))).toBeNull();
    storeMeeting(queryClient, "team-1", { ...meeting, id: "meeting-2" });
    expect(queryClient.getQueryData(queryKeys.activeMeeting("team-1"))).toMatchObject({ id: "meeting-2" });
  });

  it("records how far the server clock is from this device", () => {
    const queryClient = new QueryClient();
    const before = Date.now();
    storeMeeting(queryClient, "team-1", meeting);
    const offset = queryClient.getQueryData<number>(queryKeys.serverClockOffset) ?? 0;
    expect(before + offset).toBeLessThanOrEqual(Date.parse(meeting.server_now));
    expect(Date.now() + offset).toBeGreaterThanOrEqual(Date.parse(meeting.server_now));
  });
});
