// Small presentational components shared across pages.

import { useEffect, useRef, useState, type ReactNode } from "react";
import type { Priority } from "../api/types";
import { formatMoney } from "../lib/money";
import { label } from "../lib/labels";

/** Priority is shown by colour AND by its word, so it never depends on colour alone. */
export function PriorityBadge({ priority }: { priority: Priority }) {
  return (
    <span className={`badge priority-${priority}`}>
      <span className="dot" aria-hidden="true" />
      {label(priority)}
    </span>
  );
}

export function Tag({ children }: { children: ReactNode }) {
  return <span className="tag">{children}</span>;
}

export function MoneyText({
  amount,
  currency,
  sign,
}: {
  amount: string;
  currency: string;
  sign?: "income" | "expense";
}) {
  const prefix = sign === "income" ? "+" : sign === "expense" ? "−" : "";
  return (
    <span className={`money ${sign ?? ""}`}>
      {prefix}
      {formatMoney(amount, currency)}
    </span>
  );
}

export function ErrorNote({ error }: { error: unknown }) {
  if (!error) return null;
  const message = error instanceof Error ? error.message : "Something went wrong.";
  return (
    <p className="error-note" role="alert">
      {message}
    </p>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="empty">{children}</p>;
}

export function Spinner() {
  return (
    <p className="muted" role="status">
      Loading…
    </p>
  );
}

/** Native <dialog>: focus trapping, Esc to close and the backdrop come for free. */
export function Modal({
  open,
  title,
  onClose,
  children,
}: {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
      // showModal() focuses the first focusable element (the × button). Move focus to the
      // field marked data-autofocus (or the first field): that's where the user types.
      const target =
        dialog.querySelector<HTMLElement>("[data-autofocus]") ??
        dialog.querySelector<HTMLElement>("form input, form textarea, form select");
      target?.focus();
    }
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog ref={ref} className="modal" onClose={onClose} aria-labelledby="modal-title">
      <header className="modal-header">
        <h2 id="modal-title">{title}</h2>
        <button type="button" className="icon-button" onClick={onClose} aria-label="Close">
          ×
        </button>
      </header>
      {open && children}
    </dialog>
  );
}

export function Pagination({
  total,
  limit,
  offset,
  onChange,
}: {
  total: number;
  limit: number;
  offset: number;
  onChange: (offset: number) => void;
}) {
  if (total <= limit) return null;
  const page = Math.floor(offset / limit) + 1;
  const pages = Math.ceil(total / limit);
  return (
    <nav className="pagination" aria-label="Pagination">
      <button type="button" disabled={offset === 0} onClick={() => onChange(offset - limit)}>
        ← Previous
      </button>
      <span>
        Page {page} of {pages} · {total} items
      </span>
      <button
        type="button"
        disabled={offset + limit >= total}
        onClick={() => onChange(offset + limit)}
      >
        Next →
      </button>
    </nav>
  );
}

/** Wait until typing pauses before using a value (e.g. search box → API call). */
export function useDebounced<T>(value: T, delayMs = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = window.setTimeout(() => setDebounced(value), delayMs);
    return () => window.clearTimeout(id);
  }, [value, delayMs]);
  return debounced;
}
