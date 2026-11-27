import { describe, expect, it } from "vitest";

import { formatClock, nextSection, sectionTime } from "./meeting-clock";

const section = { startedAt: "2026-11-11T15:00:00Z", endsAt: "2026-11-11T15:05:00Z" };
const at = (iso: string) => Date.parse(iso);

describe("sectionTime", () => {
  it("counts down to the section's end, rounding up to whole seconds", () => {
    expect(sectionTime(section, at("2026-11-11T15:00:00Z"))).toEqual({ overTime: false, seconds: 300 });
    expect(sectionTime(section, at("2026-11-11T15:04:59.200Z"))).toEqual({ overTime: false, seconds: 1 });
  });

  it("never shows more time than the section has when this device lags the server", () => {
    expect(sectionTime(section, at("2026-11-11T14:59:59.700Z"))).toEqual({ overTime: false, seconds: 300 });
  });

  it("counts up once the section runs over", () => {
    expect(sectionTime(section, at("2026-11-11T15:05:00Z"))).toEqual({ overTime: true, seconds: 0 });
    expect(sectionTime(section, at("2026-11-11T15:07:13.900Z"))).toEqual({ overTime: true, seconds: 133 });
  });
});

describe("formatClock", () => {
  it("shows minutes and two-digit seconds", () => {
    expect(formatClock(0)).toBe("0:00");
    expect(formatClock(133)).toBe("2:13");
    expect(formatClock(3600)).toBe("60:00");
  });
});

describe("nextSection", () => {
  it("follows the agenda and stops after Conclude", () => {
    expect(nextSection("scorecard")).toBe("ids");
    expect(nextSection("ids")).toBe("conclude");
    expect(nextSection("conclude")).toBeNull();
  });
});
