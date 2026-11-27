import type { Schemas } from "./api/client";

export type MeetingSection = Schemas["MeetingSection"];

export const AGENDA: readonly { section: MeetingSection; label: string; minutes: number }[] = [
  { section: "scorecard", label: "Scorecard", minutes: 5 },
  { section: "ids", label: "IDS", minutes: 60 },
  { section: "conclude", label: "Conclude", minutes: 10 },
];

export const SECTION_LABELS: Record<MeetingSection, string> = {
  scorecard: "Scorecard",
  ids: "IDS",
  conclude: "Conclude",
};

export const nextSection = (section: MeetingSection): MeetingSection | null => {
  const index = AGENDA.findIndex((item) => item.section === section);
  return AGENDA[index + 1]?.section ?? null;
};

export type SectionTime = { overTime: boolean; seconds: number };

export function sectionTime(
  { startedAt, endsAt }: { startedAt: string; endsAt: string },
  serverNowMs: number,
): SectionTime {
  const endsMs = Date.parse(endsAt);
  const leftMs = Math.min(endsMs - serverNowMs, endsMs - Date.parse(startedAt));
  return leftMs > 0
    ? { overTime: false, seconds: Math.ceil(leftMs / 1000) }
    : { overTime: true, seconds: Math.floor((serverNowMs - endsMs) / 1000) };
}

export function formatClock(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}
