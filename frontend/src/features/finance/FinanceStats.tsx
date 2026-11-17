import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../../api/client";
import { ErrorNote, MoneyText, Spinner } from "../../components/ui";
import {
  addMonthsISO,
  formatDate,
  formatMonth,
  monthEnd,
  monthStart,
  todayISO,
} from "../../lib/dates";
import { label } from "../../lib/labels";
import { formatMoney, toChartNumber } from "../../lib/money";
import { CHART_COLORS, useTheme } from "../../lib/theme";

type Preset = "month" | "3months" | "year" | "lastyear";

function rangeFor(preset: Preset, today: string): { date_from: string; date_to: string } {
  const year = Number(today.slice(0, 4));
  switch (preset) {
    case "month":
      return { date_from: monthStart(today), date_to: monthEnd(today) };
    case "3months":
      return { date_from: addMonthsISO(today, -2), date_to: monthEnd(today) };
    case "year":
      return { date_from: `${year}-01-01`, date_to: `${year}-12-31` };
    case "lastyear":
      return { date_from: `${year - 1}-01-01`, date_to: `${year - 1}-12-31` };
  }
}

const PRESETS: { value: Preset; text: string }[] = [
  { value: "month", text: "This month" },
  { value: "3months", text: "Last 3 months" },
  { value: "year", text: "This year" },
  { value: "lastyear", text: "Last year" },
];

export default function FinanceStats() {
  const [preset, setPreset] = useState<Preset>("year");
  const range = rangeFor(preset, todayISO());
  const { theme } = useTheme();
  const colors = CHART_COLORS[theme];

  const stats = useQuery({
    queryKey: ["stats", range],
    queryFn: () => api.financeStats(range),
  });

  if (stats.isPending) return <Spinner />;
  if (stats.error || !stats.data) return <ErrorNote error={stats.error} />;
  const s = stats.data;
  const money = (v: string) => formatMoney(v, s.currency);

  // Recharts draws with numbers; the labels and tooltips still show the exact strings.
  const monthly = s.by_month.map((m) => ({
    month: formatMonth(m.month),
    Income: toChartNumber(m.income),
    Expense: toChartNumber(m.expense),
    raw: m,
  }));
  const categories = [...s.by_category]
    .sort((a, b) => toChartNumber(b.expense) - toChartNumber(a.expense))
    .map((c) => ({ name: label(c.category), Expense: toChartNumber(c.expense), raw: c }));
  const hasData = s.total_income !== "0.00" || s.total_expense !== "0.00";

  const axisColor = "var(--text-muted)";
  const tooltipStyle = {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 8,
    color: "var(--text)",
  };

  return (
    <section aria-label="Finance statistics">
      <div className="toolbar">
        <div className="segmented" role="radiogroup" aria-label="Date range">
          {PRESETS.map((p) => (
            <label key={p.value} className={preset === p.value ? "active" : ""}>
              <input
                type="radio"
                name="range"
                value={p.value}
                checked={preset === p.value}
                onChange={() => setPreset(p.value)}
              />
              {p.text}
            </label>
          ))}
        </div>
        <span className="muted push-right">
          {formatDate(s.date_from)} – {formatDate(s.date_to)} · paid entries only
        </span>
      </div>

      <div className="tiles">
        <div className="tile">
          <div className="tile-label">Income</div>
          <div className="tile-value">{money(s.total_income)}</div>
        </div>
        <div className="tile">
          <div className="tile-label">Expenses</div>
          <div className="tile-value">{money(s.total_expense)}</div>
        </div>
        <div className="tile">
          <div className="tile-label">Net</div>
          <div className={`tile-value ${s.net.startsWith("-") ? "negative" : ""}`}>
            {money(s.net)}
          </div>
        </div>
      </div>

      {!hasData ? (
        <p className="empty">No paid entries in this range yet.</p>
      ) : (
        <div className="charts">
          <figure className="card chart-card">
            <figcaption>Income vs expenses by month</figcaption>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={monthly} barGap={2} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke="var(--border)" />
                <XAxis dataKey="month" tick={{ fill: axisColor, fontSize: 12 }} tickLine={false} />
                <YAxis
                  tick={{ fill: axisColor, fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                  width={70}
                  tickFormatter={(v: number) =>
                    new Intl.NumberFormat(undefined, { notation: "compact" }).format(v)
                  }
                />
                <Tooltip
                  contentStyle={tooltipStyle}
                  cursor={{ fill: "var(--hover)" }}
                  formatter={(_value, name, item) => {
                    const raw = (item.payload as (typeof monthly)[number]).raw;
                    return [money(name === "Income" ? raw.income : raw.expense), name];
                  }}
                />
                <Legend wrapperStyle={{ color: "var(--text-muted)", fontSize: 13 }} />
                <Bar dataKey="Income" fill={colors.income} radius={[4, 4, 0, 0]} maxBarSize={28} />
                <Bar
                  dataKey="Expense"
                  fill={colors.expense}
                  radius={[4, 4, 0, 0]}
                  maxBarSize={28}
                />
              </BarChart>
            </ResponsiveContainer>
          </figure>

          <figure className="card chart-card">
            <figcaption>Where the money went (expenses by type)</figcaption>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart
                data={categories}
                layout="vertical"
                margin={{ top: 0, right: 16, left: 8, bottom: 0 }}
              >
                <XAxis type="number" hide />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fill: axisColor, fontSize: 13 }}
                  tickLine={false}
                  axisLine={false}
                  width={110}
                />
                <Tooltip
                  contentStyle={tooltipStyle}
                  cursor={{ fill: "var(--hover)" }}
                  formatter={(_value, _name, item) => [
                    money((item.payload as (typeof categories)[number]).raw.expense),
                    "Spent",
                  ]}
                />
                <Bar dataKey="Expense" fill={colors.single} radius={[0, 4, 4, 0]} maxBarSize={24} />
              </BarChart>
            </ResponsiveContainer>
            {/* The same numbers as a table: readable by screen readers and in print. */}
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Type</th>
                  <th scope="col" className="num">
                    Spent
                  </th>
                  <th scope="col" className="num">
                    Earned
                  </th>
                </tr>
              </thead>
              <tbody>
                {categories.map((c) => (
                  <tr key={c.name}>
                    <th scope="row">{c.name}</th>
                    <td className="num">
                      <MoneyText amount={c.raw.expense} currency={s.currency} />
                    </td>
                    <td className="num">
                      <MoneyText amount={c.raw.income} currency={s.currency} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </figure>
        </div>
      )}
    </section>
  );
}
