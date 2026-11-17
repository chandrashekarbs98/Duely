import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";
import { api } from "../api/client";
import type { MonthSummary } from "../api/types";
import { useUser } from "../auth/AuthProvider";
import { Empty, ErrorNote, MoneyText, Spinner } from "../components/ui";
import FinanceItem from "../features/finance/FinanceItem";
import TodoItem from "../features/todos/TodoItem";
import { formatDate, formatMonth } from "../lib/dates";
import { useDataMutation } from "../lib/queries";

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

function BudgetCard({ month, currency }: { month: MonthSummary; currency: string }) {
  const used = month.budget_used_percent;
  const tone = used === null ? "" : used >= 100 ? "over" : used >= 80 ? "near" : "ok";
  return (
    <section className="card" aria-labelledby="month-title">
      <h2 id="month-title">{formatMonth(month.month, "long")} at a glance</h2>
      <dl className="summary">
        <div>
          <dt>Income</dt>
          <dd>
            <MoneyText amount={month.income} currency={currency} />
          </dd>
        </div>
        <div>
          <dt>Spent</dt>
          <dd>
            <MoneyText amount={month.expense} currency={currency} />
          </dd>
        </div>
        <div>
          <dt>Net</dt>
          <dd className={month.net.startsWith("-") ? "negative" : ""}>
            <MoneyText amount={month.net} currency={currency} />
          </dd>
        </div>
      </dl>
      {month.budget && used !== null && month.budget_remaining ? (
        <div className="budget">
          <div className="budget-text">
            <span>
              Budget <MoneyText amount={month.budget} currency={currency} />
            </span>
            <span className={`budget-status ${tone}`}>
              {used}% used ·{" "}
              {month.budget_remaining.startsWith("-") ? (
                <>
                  over by <MoneyText amount={month.budget_remaining.slice(1)} currency={currency} />
                </>
              ) : (
                <>
                  <MoneyText amount={month.budget_remaining} currency={currency} /> left
                </>
              )}
            </span>
          </div>
          <div
            className="progress"
            role="progressbar"
            aria-label="Monthly budget used"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.min(used, 100)}
          >
            <div className={`progress-bar ${tone}`} style={{ width: `${Math.min(used, 100)}%` }} />
          </div>
        </div>
      ) : (
        <p className="muted">
          <Link to="/settings">Set a monthly budget</Link> to track spending against it.
        </p>
      )}
    </section>
  );
}

export default function HomePage() {
  const user = useUser();
  const home = useQuery({ queryKey: ["home"], queryFn: api.home });
  const toggle = useDataMutation((id: number) => api.toggleTodo(id));
  const pay = useDataMutation((id: number) => api.payFinance(id));

  if (home.isPending) return <Spinner />;
  if (home.error || !home.data) return <ErrorNote error={home.error} />;
  const h = home.data;

  return (
    <>
      <div className="page-header">
        <div>
          <h1>
            {greeting()}, {user.name.split(" ")[0]}
          </h1>
          <p className="muted">{formatDate(h.today)}</p>
        </div>
      </div>

      <div className="tiles">
        <Link className="tile link-tile" to="/dashboard?tab=todos">
          <div className="tile-label">Open to-dos</div>
          <div className="tile-value">{h.counts.open_todos}</div>
        </Link>
        <Link className="tile link-tile" to="/reminders">
          <div className="tile-label">Overdue</div>
          <div className={`tile-value ${h.counts.overdue_todos > 0 ? "negative" : ""}`}>
            {h.counts.overdue_todos}
          </div>
        </Link>
        <div className="tile">
          <div className="tile-label">Done this week</div>
          <div className="tile-value">{h.counts.completed_this_week}</div>
        </div>
      </div>

      <ErrorNote error={toggle.error ?? pay.error} />
      <div className="grid-2">
        <section className="card" aria-labelledby="urgent-title">
          <div className="card-header">
            <h2 id="urgent-title">Urgent to-dos</h2>
            <Link to="/dashboard?tab=todos">All to-dos →</Link>
          </div>
          <p className="muted small">High priority, due today, or overdue.</p>
          {h.urgent_todos.length === 0 ? (
            <Empty>Nothing urgent. Nice work.</Empty>
          ) : (
            <ul className="list compact">
              {h.urgent_todos.map((todo) => (
                <TodoItem
                  key={todo.id}
                  todo={todo}
                  today={h.today}
                  onToggle={(t) => toggle.mutate(t.id)}
                />
              ))}
            </ul>
          )}
        </section>

        <div className="stack">
          <BudgetCard month={h.month} currency={h.currency} />
          <section className="card" aria-labelledby="bills-title">
            <div className="card-header">
              <h2 id="bills-title">Bills due in the next 7 days</h2>
              <Link to="/dashboard?tab=finance&view=list">Finance →</Link>
            </div>
            {h.upcoming_payments.length === 0 ? (
              <Empty>No planned payments this week.</Empty>
            ) : (
              <ul className="list compact">
                {h.upcoming_payments.map((entry) => (
                  <FinanceItem
                    key={entry.id}
                    entry={entry}
                    currency={h.currency}
                    today={h.today}
                    onPay={(e) => pay.mutate(e.id)}
                  />
                ))}
              </ul>
            )}
          </section>
        </div>
      </div>
    </>
  );
}
