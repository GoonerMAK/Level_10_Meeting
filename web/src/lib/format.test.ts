import { describe, expect, it } from "vitest";

import { ApiError } from "./api/errors";
import { formatDate, formatDateTime, formatDuration, formatGoal, formatQuarter, formatRating, formatValue } from "./format";
import { splitServerErrors } from "./forms";
import { scoreValueSchema, toPriority, toPriorityChoice } from "./validation";

describe("formatValue and formatGoal", () => {
  it("writes each seeded unit the way people read it", () => {
    expect(formatValue(12, "count")).toBe("12");
    expect(formatValue(2.5, "%")).toBe("2.5%");
    expect(formatValue(3, "hours")).toBe("3 h");
    expect(formatValue(1250, "$k")).toBe("$1,250k");
  });

  it("writes every goal type", () => {
    const goal = { value: null, min: null, max: null };
    expect(formatGoal({ ...goal, type: "at_least", value: 10 }, "count")).toBe("≥ 10");
    expect(formatGoal({ ...goal, type: "at_most", value: 3 }, "%")).toBe("≤ 3%");
    expect(formatGoal({ ...goal, type: "exactly", value: 1 }, "count")).toBe("= 1");
    expect(formatGoal({ ...goal, type: "between", min: 2, max: 4 }, "hours")).toBe("2 h – 4 h");
  });
});

describe("dates", () => {
  it("shows a time in the company time zone, so a late Sunday stays on Sunday", () => {
    expect(formatDateTime("2026-11-09T05:58:00Z", "America/Chicago")).toBe("Nov 8, 11:58 PM CST");
  });

  it("writes the quarter the way people say it", () => {
    expect(formatQuarter("2026-Q4")).toBe("Q4 2026");
  });

  it("shows a calendar date as written, whatever the viewer's zone", () => {
    expect(formatDate("2026-11-18")).toBe("Nov 18");
  });
});

describe("form helpers", () => {
  it("puts server field errors on their fields and the rest on the form", () => {
    const error = new ApiError({
      status: 422,
      code: "invalid_input",
      message: "Owner must be a Team Member of this team or an Admin",
      fields: [{ field: "owner_id", message: "Owner must be a Team Member of this team or an Admin" }],
    });

    expect(splitServerErrors(error, { owner_id: "ownerId" })).toEqual({
      fieldErrors: [["ownerId", "Owner must be a Team Member of this team or an Admin"]],
      formError: null,
    });
    expect(splitServerErrors(error, {}).formError).toBe("Owner must be a Team Member of this team or an Admin");
  });

  it("accepts scores the API stores and rejects the rest", () => {
    expect(scoreValueSchema.safeParse("12.5").success).toBe(true);
    expect(scoreValueSchema.safeParse(" -3 ").success).toBe(true);
    expect(scoreValueSchema.safeParse("1.23456").success).toBe(false);
    expect(scoreValueSchema.safeParse("ten").success).toBe(false);
  });

  it("maps priority choices both ways", () => {
    expect(toPriority("none")).toBeNull();
    expect(toPriority("5")).toBe(5);
    expect(toPriorityChoice(null)).toBe("none");
    expect(toPriorityChoice(3)).toBe("3");
  });
});

describe("meeting summary formats", () => {
  it("shows a rating to one decimal", () => {
    expect(formatRating(8)).toBe("8.0");
    expect(formatRating(7.5)).toBe("7.5");
  });

  it("shows how long a meeting ran in minutes, then hours", () => {
    expect(formatDuration("2026-11-11T15:00:00Z", "2026-11-11T15:00:20Z")).toBe("Under 1 min");
    expect(formatDuration("2026-11-11T15:00:00Z", "2026-11-11T15:47:20Z")).toBe("47 min");
    expect(formatDuration("2026-11-11T15:00:00Z", "2026-11-11T16:00:00Z")).toBe("1 h");
    expect(formatDuration("2026-11-11T15:00:00Z", "2026-11-11T16:15:00Z")).toBe("1 h 15 min");
  });
});
