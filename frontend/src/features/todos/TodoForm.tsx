import { useState, type FormEvent } from "react";
import type { Category, Period, Priority, Todo, TodoInput } from "../../api/types";
import { ErrorNote } from "../../components/ui";
import { CATEGORIES, PERIODS, PRIORITIES, label } from "../../lib/labels";

interface Props {
  initial?: Todo;
  onSubmit: (data: TodoInput) => Promise<unknown>;
  onCancel: () => void;
}

export default function TodoForm({ initial, onSubmit, onCancel }: Props) {
  const [title, setTitle] = useState(initial?.title ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [period, setPeriod] = useState<Period>(initial?.period ?? "daily");
  const [priority, setPriority] = useState<Priority>(initial?.priority ?? "medium");
  const [category, setCategory] = useState<Category>(initial?.category ?? "misc");
  const [dueDate, setDueDate] = useState(initial?.due_date ?? "");
  const [error, setError] = useState<unknown>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await onSubmit({
        title: title.trim(),
        description: description.trim() || null,
        period,
        priority,
        category,
        due_date: dueDate || null,
      });
    } catch (err) {
      setError(err);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <label>
        Title
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          maxLength={200}
          data-autofocus
        />
      </label>
      <label>
        Notes <span className="muted">(optional)</span>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={2000}
          rows={3}
        />
      </label>
      <div className="form-row">
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
      </div>
      <div className="form-row">
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
        <label>
          Due date <span className="muted">(optional)</span>
          <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
        </label>
      </div>
      <ErrorNote error={error} />
      <div className="form-actions">
        <button type="button" className="ghost" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" className="primary" disabled={saving}>
          {saving ? "Saving…" : initial ? "Save changes" : "Add to-do"}
        </button>
      </div>
    </form>
  );
}
