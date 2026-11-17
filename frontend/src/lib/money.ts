// Money arrives as a decimal string ("1234.5" or "1234.50"). We format it by working on the
// digits as text (and BigInt for grouping), so no floating-point number is ever involved.

const MONEY_PATTERN = /^\d{1,10}(\.\d{1,2})?$/;

/** True for what the backend accepts: positive, up to 10 digits, at most 2 decimals. */
export function isValidMoneyInput(value: string): boolean {
  return MONEY_PATTERN.test(value.trim()) && !/^0+(\.0+)?$/.test(value.trim());
}

function localeFor(currency: string): string {
  // Fixed locales so formatting is the same on every machine. en-IN groups as 1,00,000.
  return currency === "INR" ? "en-IN" : "en-US";
}

function currencySymbol(currency: string): string {
  try {
    const parts = new Intl.NumberFormat(localeFor(currency), {
      style: "currency",
      currency,
      currencyDisplay: "narrowSymbol",
    }).formatToParts(0);
    return parts.find((p) => p.type === "currency")?.value ?? currency;
  } catch {
    return currency;
  }
}

export function formatMoney(amount: string, currency: string): string {
  const trimmed = amount.trim();
  const negative = trimmed.startsWith("-");
  const [intPart = "0", fracPart = ""] = trimmed.replace(/^[-+]/, "").split(".");
  const grouped = new Intl.NumberFormat(localeFor(currency)).format(BigInt(intPart || "0"));
  const cents = (fracPart + "00").slice(0, 2);
  return `${negative ? "-" : ""}${currencySymbol(currency)}${grouped}.${cents}`;
}

/** Charts need numbers. Only used for drawing bars, never for arithmetic shown to the user. */
export function toChartNumber(amount: string): number {
  return Number(amount);
}
