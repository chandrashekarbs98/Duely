import { useState, type FormEvent } from "react";
import type {
  Category,
  EntryKind,
  EntryStatus,
  FinanceEntry,
  FinanceInput,
  Period,
  Priority,
} from "../../api/types";
import { ErrorNote } from "../../components/ui";
import { todayISO } from "../../lib/dates";
import { CATEGORIES, PERIODS, PRIORITIES, label } from "../../lib/labels";
import { isValidMoneyInput } from "../../lib/money";

interface Props {
  initial?: FinanceEntry;
  currency: string;
  onSubmit: (data: FinanceInput) => Promise<unknown>;
  onCancel: () => void;
}

export default function FinanceForm({ initial, currency, onSubmit, onCancel }: Props) {
  const [title, setTitle] = useState(initial?.title ?? "");
  const [kind, setKind] = useState<EntryKind>(initial?.kind ?? "expense");
  const [amount, setAmount] = useState(initial?.amount ?? "");
  const [entryDate, setEntryDate] = useState(initial?.entry_date ?? todayISO());
  const [status, setStatus] = useState<EntryStatus>(initial?.status ?? "paid");
  const [period, setPeriod] = useState<Period>(initial?.period ?? "daily");
  const [priority, setPriority] = useState<Priority>(initial?.priority ?? "medium");
  const [category, setCategory] = useState<Category>(initial?.category ?? "misc");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [error, setError] = useState<unknown>(null);
  const [saving, setSaving] = useState(false);

  const amountOk = amount === "" || isValidMoneyInput(amount);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!isValidMoneyInput(amount)) {
      setError(new Error("Enter an amount greater than 0 with at most 2 decimals."));
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSubmit({
        title: title.trim(),
        description: description.trim() || null,
        kind,
        amount: amount.trim(), // sent as a string; the server stores it as NUMERIC
        entry_date: entryDate,
        status,
        period,
        priority,
        category,
      });
    } catch (err) {
      setError(err);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <div className="segmented" role="radiogroup" aria-label="Kind">
        {(["expense", "income"] as const).map((k) => (
          <label key={k} className={kind === k ? "active" : ""}>
            <input
              type="radio"
              name="kind"
              value={k}
              checked={kind === k}
              onChange={() => setKind(k)}
            />
            {label(k)}
          </label>
        ))}
      </div>
      <label>
        Title
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          maxLength={200}
          placeholder={kind === "expense" ? "e.g. Groceries, Netflix" : "e.g. Salary"}
          data-autofocus
        />
      </label>
      <div className="form-row">
        <label>
          Amount ({currency})
          <input
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            inputMode="decimal"
            placeholder="0.00"
            required
            aria-invalid={!amountOk}
          />
        </label>
        <label>
          Date
          <input
            type="date"
            value={entryDate}
            onChange={(e) => setEntryDate(e.target.value)}
            required
          />
        </label>
      </div>
      <div className="form-row">
        <label>
          Status
          <select value={status} onChange={(e) => setStatus(e.target.value as EntryStatus)}>
            <option value="paid">Paid (already happened)</option>
            <option value="planned">Planned (upcoming bill)</option>
          </select>
        </label>
        <label>
          Period
          <select value={period} onChange={(e) => setPeriod(e.target.value as Period)}>
            {PERIODS.map((p) => (
              <option key={p} value={p}>
                {label(p)}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="form-row">
        <label>
          Type
          <select value={category} onChange={(e) => setCategory(e.target.value as Category)}>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {label(c)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Priority
          <select value={priority} onChange={(e) => setPriority(e.target.value as Priority)}>
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {label(p)}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label>
        Notes <span className="muted">(optional)</span>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={2000}
          rows={2}
        />
      </label>
      <ErrorNote error={error} />
      <div className="form-actions">
        <button type="button" className="ghost" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" className="primary" disabled={saving}>
          {saving ? "Saving…" : initial ? "Save changes" : "Add entry"}
        </button>
      </div>
    </form>
  );
}
