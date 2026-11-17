import type { Category, EntryKind, EntryStatus, Period, Priority } from "../api/types";

export const PERIODS: Period[] = ["daily", "monthly", "yearly"];
export const PRIORITIES: Priority[] = ["high", "medium", "low"];
export const CATEGORIES: Category[] = ["home", "office", "self", "misc"];
export const KINDS: EntryKind[] = ["expense", "income"];
export const STATUSES: EntryStatus[] = ["paid", "planned"];

const NAMES: Record<string, string> = {
  daily: "Daily",
  monthly: "Monthly",
  yearly: "Yearly",
  high: "High",
  medium: "Medium",
  low: "Low",
  home: "Home",
  office: "Office",
  self: "Self",
  misc: "Miscellaneous",
  expense: "Expense",
  income: "Income",
  paid: "Paid",
  planned: "Planned",
};

export function label(value: string): string {
  return NAMES[value] ?? value;
}
