import type { FinanceEntry } from "../../api/types";
import { MoneyText, PriorityBadge, Tag } from "../../components/ui";
import { dueLabel, formatDate, todayISO } from "../../lib/dates";
import { label } from "../../lib/labels";

interface Props {
  entry: FinanceEntry;
  currency: string;
  today?: string;
  onPay?: (entry: FinanceEntry) => void;
  onEdit?: (entry: FinanceEntry) => void;
  onRepeat?: (entry: FinanceEntry) => void;
  onDelete?: (entry: FinanceEntry) => void;
}

export default function FinanceItem({
  entry,
  currency,
  today,
  onPay,
  onEdit,
  onRepeat,
  onDelete,
}: Props) {
  const planned = entry.status === "planned";
  const due = planned ? dueLabel(entry.entry_date, today ?? todayISO()) : null;
  return (
    <li className="item">
      <div className="item-date">{formatDate(entry.entry_date)}</div>
      <div className="item-body">
        <div className="item-title">{entry.title}</div>
        {entry.description && <div className="item-desc">{entry.description}</div>}
        <div className="item-meta">
          <PriorityBadge priority={entry.priority} />
          <Tag>{label(entry.category)}</Tag>
          <Tag>{label(entry.period)}</Tag>
          {planned && <span className={`due due-${due?.tone ?? "later"}`}>{due?.text}</span>}
        </div>
      </div>
      <div className="item-amount">
        <MoneyText amount={entry.amount} currency={currency} sign={entry.kind} />
        <span className={`status status-${entry.status}`}>{label(entry.status)}</span>
      </div>
      <div className="item-actions">
        {planned && onPay && (
          <button type="button" className="link" onClick={() => onPay(entry)}>
            Mark paid
          </button>
        )}
        {onEdit && (
          <button type="button" className="link" onClick={() => onEdit(entry)}>
            Edit
          </button>
        )}
        {onRepeat && (
          <button
            type="button"
            className="link"
            onClick={() => onRepeat(entry)}
            title="Copy as a planned entry for the next period"
          >
            Repeat
          </button>
        )}
        {onDelete && (
          <button type="button" className="link danger" onClick={() => onDelete(entry)}>
            Delete
          </button>
        )}
      </div>
    </li>
  );
}
