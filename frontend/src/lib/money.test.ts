import { describe, expect, it } from "vitest";
import { formatMoney, isValidMoneyInput } from "./money";

describe("formatMoney", () => {
  it("keeps the exact digits", () => {
    expect(formatMoney("199.99", "INR")).toBe("₹199.99");
    expect(formatMoney("0.30", "INR")).toBe("₹0.30");
  });

  it("pads missing cents", () => {
    expect(formatMoney("5", "INR")).toBe("₹5.00");
    expect(formatMoney("5.5", "INR")).toBe("₹5.50");
  });

  it("uses Indian digit grouping for INR", () => {
    expect(formatMoney("1234567.89", "INR")).toBe("₹12,34,567.89");
  });

  it("handles negatives and very large values without float rounding", () => {
    expect(formatMoney("-650.00", "INR")).toBe("-₹650.00");
    expect(formatMoney("9999999999.99", "USD")).toBe("$9,999,999,999.99");
  });
});

describe("isValidMoneyInput", () => {
  it("accepts what the backend accepts", () => {
    expect(isValidMoneyInput("199.99")).toBe(true);
    expect(isValidMoneyInput("10")).toBe(true);
  });

  it("rejects zero, negatives, too many decimals and junk", () => {
    for (const bad of ["0", "0.00", "-5", "10.999", "abc", "", "1e5"]) {
      expect(isValidMoneyInput(bad)).toBe(false);
    }
  });
});
