import { describe, expect, it } from "vitest";
import { addMonthsISO, daysBetween, dueLabel, monthEnd, monthStart } from "./dates";

describe("dates", () => {
  it("counts days across month and year boundaries", () => {
    expect(daysBetween("2026-12-31", "2027-01-01")).toBe(1);
    expect(daysBetween("2026-03-15", "2026-03-10")).toBe(-5);
  });

  it("labels due dates relative to today", () => {
    const today = "2026-03-15";
    expect(dueLabel("2026-03-14", today)).toEqual({ text: "Overdue by 1 day", tone: "overdue" });
    expect(dueLabel("2026-03-15", today).tone).toBe("today");
    expect(dueLabel("2026-03-16", today).text).toBe("Due tomorrow");
    expect(dueLabel("2026-03-20", today).text).toBe("Due in 5 days");
    expect(dueLabel("2026-04-30", today).tone).toBe("later");
  });

  it("finds month boundaries", () => {
    expect(monthStart("2026-02-17")).toBe("2026-02-01");
    expect(monthEnd("2026-02-17")).toBe("2026-02-28");
    expect(monthEnd("2028-02-01")).toBe("2028-02-29");
    expect(addMonthsISO("2026-01-15", -2)).toBe("2025-11-01");
  });
});
