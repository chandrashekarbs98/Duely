import type { Todo } from "../../api/types";
import { PriorityBadge, Tag } from "../../components/ui";
import { dueLabel, todayISO } from "../../lib/dates";
import { label } from "../../lib/labels";

interface Props {
  todo: Todo;
  today?: string;
  onToggle: (todo: Todo) => void;
  onEdit?: (todo: Todo) => void;
  onRepeat?: (todo: Todo) => void;
  onDelete?: (todo: Todo) => void;
}

/** One row. Used on the Dashboard, Home and Reminders pages. */
export default function TodoItem({ todo, today, onToggle, onEdit, onRepeat, onDelete }: Props) {
  const due = todo.due_date ? dueLabel(todo.due_date, today ?? todayISO()) : null;
  return (
    <li className={`item ${todo.completed ? "done" : ""}`}>
      <input
        type="checkbox"
        className="check"
        checked={todo.completed}
        onChange={() => onToggle(todo)}
        aria-label={`Mark "${todo.title}" as ${todo.completed ? "not done" : "done"}`}
      />
      <div className="item-body">
        <div className="item-title">{todo.title}</div>
        {todo.description && <div className="item-desc">{todo.description}</div>}
        <div className="item-meta">
          <PriorityBadge priority={todo.priority} />
          <Tag>{label(todo.category)}</Tag>
          <Tag>{label(todo.period)}</Tag>
          {due && !todo.completed && <span className={`due due-${due.tone}`}>{due.text}</span>}
        </div>
      </div>
      {(onEdit || onRepeat || onDelete) && (
        <div className="item-actions">
          {onEdit && (
            <button type="button" className="link" onClick={() => onEdit(todo)}>
              Edit
            </button>
          )}
          {onRepeat && (
            <button
              type="button"
              className="link"
              onClick={() => onRepeat(todo)}
              title={`Copy to next ${todo.period === "daily" ? "day" : todo.period.replace("ly", "")}`}
            >
              Repeat
            </button>
          )}
          {onDelete && (
            <button type="button" className="link danger" onClick={() => onDelete(todo)}>
              Delete
            </button>
          )}
        </div>
      )}
    </li>
  );
}
