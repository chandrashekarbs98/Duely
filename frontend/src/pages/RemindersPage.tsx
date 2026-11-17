import { useMutation, useQuery } from "@tanstack/react-query";
import { Link } from "react-router";
import { api } from "../api/client";
import type { FinanceEntry, Todo } from "../api/types";
import { useAuth, useUser } from "../auth/AuthProvider";
import { Empty, ErrorNote, Spinner } from "../components/ui";
import FinanceItem from "../features/finance/FinanceItem";
import TodoItem from "../features/todos/TodoItem";
import { useDataMutation } from "../lib/queries";

function Section({
  title,
  tone,
  todos,
  payments,
  today,
  currency,
  onToggle,
  onPay,
}: {
  title: string;
  tone: "overdue" | "today" | "soon";
  todos: Todo[];
  payments: FinanceEntry[];
  today: string;
  currency: string;
  onToggle: (t: Todo) => void;
  onPay: (e: FinanceEntry) => void;
}) {
  const count = todos.length + payments.length;
  return (
    <section className={`card reminder-${tone}`} aria-label={title}>
      <div className="card-header">
        <h2>
          {title} <span className="count">{count}</span>
        </h2>
      </div>
      {count === 0 ? (
        <Empty>Nothing here.</Empty>
      ) : (
        <ul className="list compact">
          {todos.map((t) => (
            <TodoItem key={`t${t.id}`} todo={t} today={today} onToggle={onToggle} />
          ))}
          {payments.map((p) => (
            <FinanceItem
              key={`p${p.id}`}
              entry={p}
              currency={currency}
              today={today}
              onPay={onPay}
            />
          ))}
        </ul>
      )}
    </section>
  );
}

function EmailReminders() {
  const user = useUser();
  const { setUser } = useAuth();
  const setting = useMutation({
    mutationFn: (on: boolean) => api.updateMe({ email_reminders: on }),
    onSuccess: setUser,
  });
  const test = useMutation({ mutationFn: api.sendTestEmail });

  return (
    <section className="card" aria-labelledby="email-title">
      <h2 id="email-title">Email reminders</h2>
      <p className="muted">
        A short digest each morning of what's overdue, due today, and due this week. Sent only when
        something needs your attention.
      </p>
      <label className="switch">
        <input
          type="checkbox"
          checked={user.email_reminders}
          disabled={setting.isPending}
          onChange={(e) => setting.mutate(e.target.checked)}
        />
        Email me a daily digest at <strong>{user.email}</strong>
      </label>
      <div className="form-actions start">
        <button
          type="button"
          className="ghost"
          onClick={() => test.mutate()}
          disabled={test.isPending}
        >
          {test.isPending ? "Sending…" : "Send me a test email now"}
        </button>
        {test.data && (
          <span className="success" role="status">
            Sent to {test.data.sent_to}
          </span>
        )}
      </div>
      <ErrorNote error={setting.error ?? test.error} />
    </section>
  );
}

export default function RemindersPage() {
  const { currency } = useUser();
  const reminders = useQuery({ queryKey: ["reminders"], queryFn: api.reminders });
  const toggle = useDataMutation((id: number) => api.toggleTodo(id));
  const pay = useDataMutation((id: number) => api.payFinance(id));

  if (reminders.isPending) return <Spinner />;
  if (reminders.error || !reminders.data) return <ErrorNote error={reminders.error} />;
  const r = reminders.data;
  const common = {
    today: r.today,
    currency,
    onToggle: (t: Todo) => toggle.mutate(t.id),
    onPay: (e: FinanceEntry) => pay.mutate(e.id),
  };
  const nothing =
    r.overdue_todos.length +
      r.due_today_todos.length +
      r.upcoming_todos.length +
      r.overdue_payments.length +
      r.due_today_payments.length +
      r.upcoming_payments.length ===
    0;

  return (
    <>
      <div className="page-header">
        <h1>Reminders</h1>
        <Link to="/dashboard">Go to dashboard →</Link>
      </div>
      <ErrorNote error={toggle.error ?? pay.error} />
      {nothing && (
        <p className="empty">
          You're all caught up. Items with a due date (to-dos) or planned bills show up here.
        </p>
      )}
      <div className="stack">
        <Section
          title="Overdue"
          tone="overdue"
          todos={r.overdue_todos}
          payments={r.overdue_payments}
          {...common}
        />
        <Section
          title="Due today"
          tone="today"
          todos={r.due_today_todos}
          payments={r.due_today_payments}
          {...common}
        />
        <Section
          title="Next 7 days"
          tone="soon"
          todos={r.upcoming_todos}
          payments={r.upcoming_payments}
          {...common}
        />
        <EmailReminders />
      </div>
    </>
  );
}
