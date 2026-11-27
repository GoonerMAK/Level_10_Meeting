import type { Goal } from "./api/client";

const numberFormat = new Intl.NumberFormat("en-US", { maximumFractionDigits: 4 });

export const formatNumber = (value: number): string => numberFormat.format(value);

export function formatValue(value: number, unit: string): string {
  const number = formatNumber(value);
  switch (unit) {
    case "count":
      return number;
    case "%":
      return `${number}%`;
    case "hours":
      return `${number} h`;
    case "$k":
      return `$${number}k`;
    default:
      return `${number} ${unit}`;
  }
}

export function formatGoal(goal: Goal, unit: string): string {
  const value = (number: number | null) => (number === null ? "?" : formatValue(number, unit));
  switch (goal.type) {
    case "at_least":
      return `≥ ${value(goal.value)}`;
    case "at_most":
      return `≤ ${value(goal.value)}`;
    case "exactly":
      return `= ${value(goal.value)}`;
    case "between":
      return `${value(goal.min)} – ${value(goal.max)}`;
    default: {
      const exhaustive: never = goal.type;
      return exhaustive;
    }
  }
}

export function formatDateTime(iso: string, timeZone: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone,
    timeZoneName: "short",
  }).format(new Date(iso));
}

const calendarDate = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", timeZone: "UTC" });

export const formatDate = (isoDate: string): string => calendarDate.format(new Date(`${isoDate}T00:00:00Z`));

export const formatQuarter = (quarter: string): string => quarter.replace(/^(\d{4})-(Q[1-4])$/, "$2 $1");
