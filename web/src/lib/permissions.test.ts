import { describe, expect, it } from "vitest";

import { ApiError } from "./api/errors";
import { canChangeTeam } from "./permissions";
import { shouldRetry } from "./query-client";

describe("canChangeTeam", () => {
  it("lets Admins change every team and Team Members only their own", () => {
    expect(canChangeTeam({ role: "admin", team_ids: [] }, "team-1")).toBe(true);
    expect(canChangeTeam({ role: "team_member", team_ids: ["team-1"] }, "team-1")).toBe(true);
    expect(canChangeTeam({ role: "team_member", team_ids: ["team-1"] }, "team-2")).toBe(false);
  });

  it("keeps Observers read-only, even on their own team", () => {
    expect(canChangeTeam({ role: "observer", team_ids: ["team-1"] }, "team-1")).toBe(false);
  });
});

describe("shouldRetry", () => {
  const apiError = (status: number) => new ApiError({ status, code: "x", message: "x", fields: [] });

  it("retries server and network failures but not refusals", () => {
    expect(shouldRetry(0, apiError(503))).toBe(true);
    expect(shouldRetry(0, new TypeError("Failed to fetch"))).toBe(true);
    expect(shouldRetry(0, apiError(404))).toBe(false);
    expect(shouldRetry(2, apiError(503))).toBe(false);
  });
});
