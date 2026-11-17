// Dates are "YYYY-MM-DD" strings (calendar days, no time zone). We never pass them through
// `new Date("2026-03-15")`, which parses as UTC midnight and can show the previous day.

import type { ISODate } from "../api/types";

function parts(iso: ISODate): [number, number, number] {
  const [y = 0, m = 1, d = 1] = iso.split("-").map(Number);
  return [y, m, d];
}

export function toISODate(date: Date): ISODate {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function todayISO(): ISODate {
  return toISODate(new Date());
}

export function formatDate(iso: ISODate): string {
  const [y, m, d] = parts(iso);
  return new Date(y, m - 1, d).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

/** "2026-11" → "Nov '26" (chart axes) or "November 2026" (long). */
export function formatMonth(label: string, style: "short" | "long" = "short"): string {
  const [y, m] = parts(`${label}-01`);
  const date = new Date(y, m - 1, 1);
  if (style === "long") {
    return date.toLocaleDateString(undefined, { month: "long", year: "numeric" });
  }
  return `${date.toLocaleDateString(undefined, { month: "short" })} '${String(y).slice(2)}`;
}

/** Whole days from `from` to `to` (negative if `to` is earlier). */
export function daysBetween(from: ISODate, to: ISODate): number {
  const [y1, m1, d1] = parts(from);
  const [y2, m2, d2] = parts(to);
  return Math.round((Date.UTC(y2, m2 - 1, d2) - Date.UTC(y1, m1 - 1, d1)) / 86_400_000);
}

export type DueTone = "overdue" | "today" | "soon" | "later";

export function dueLabel(due: ISODate, today: ISODate): { text: string; tone: DueTone } {
  const diff = daysBetween(today, due);
  if (diff < 0) {
    const n = -diff;
    return { text: `Overdue by ${n} day${n === 1 ? "" : "s"}`, tone: "overdue" };
  }
  if (diff === 0) return { text: "Due today", tone: "today" };
  if (diff === 1) return { text: "Due tomorrow", tone: "soon" };
  if (diff <= 7) return { text: `Due in ${diff} days`, tone: "soon" };
  return { text: `Due ${formatDate(due)}`, tone: "later" };
}

export function addMonthsISO(iso: ISODate, months: number): ISODate {
  const [y, m] = parts(iso);
  return toISODate(new Date(y, m - 1 + months, 1));
}

export function monthStart(iso: ISODate): ISODate {
  return `${iso.slice(0, 7)}-01`;
}

export function monthEnd(iso: ISODate): ISODate {
  const [y, m] = parts(iso);
  return toISODate(new Date(y, m, 0));
}
