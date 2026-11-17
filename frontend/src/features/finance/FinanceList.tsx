import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../../api/client";
import type {
  Category,
  EntryKind,
  EntryStatus,
  FinanceEntry,
  FinanceFilters,
  FinanceInput,
  Period,
} from "../../api/types";
import { useUser } from "../../auth/AuthProvider";
import { Empty, ErrorNote, Modal, Pagination, Spinner, useDebounced } from "../../components/ui";
import { CATEGORIES, KINDS, PERIODS, STATUSES, label } from "../../lib/labels";
import { useDataMutation } from "../../lib/queries";
import FinanceForm from "./FinanceForm";
import FinanceItem from "./FinanceItem";

const LIMIT = 20;

export default function FinanceList() {
  const { currency } = useUser();
  const [search, setSearch] = useState("");
  const [kind, setKind] = useState<EntryKind | "">("");
  const [status, setStatus] = useState<EntryStatus | "">("");
  const [category, setCategory] = useState<Category | "">("");
  const [period, setPeriod] = useState<Period | "">("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [offset, setOffset] = useState(0);
  const [editing, setEditing] = useState<FinanceEntry | "new" | null>(null);

  const q = useDebounced(search.trim());
  const filters: FinanceFilters = {
    q: q || undefined,
    kind: kind || undefined,
    status: status || undefined,
    category: category || undefined,
    period: period || undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
  };
  const query = { ...filters, limit: LIMIT, offset };

  const entries = useQuery({
    queryKey: ["finances", query],
    queryFn: () => api.listFinances(query),
    placeholderData: keepPreviousData,
  });

  const create = useDataMutation((data: FinanceInput) => api.createFinance(data));
  const update = useDataMutation(({ id, data }: { id: number; data: FinanceInput }) =>
    api.updateFinance(id, data),
  );
  const pay = useDataMutation((id: number) => api.payFinance(id));
  const repeat = useDataMutation((id: number) => api.repeatFinance(id));
  const remove = useDataMutation((id: number) => api.deleteFinance(id));

  function onFilter<T>(setter: (v: T) => void) {
    return (value: T) => {
      setter(value);
      setOffset(0);
    };
  }

  async function handleSave(data: FinanceInput) {
    if (editing === "new") await create.mutateAsync(data);
    else if (editing) await update.mutateAsync({ id: editing.id, data });
    setEditing(null);
  }

  function handleDelete(entry: FinanceEntry) {
    if (window.confirm(`Delete "${entry.title}"? This cannot be undone.`)) remove.mutate(entry.id);
  }

  return (
    <section aria-label="Finance entries">
      <div className="toolbar">
        <input
          type="search"
          placeholder="Search entries…"
          value={search}
          onChange={(e) => onFilter(setSearch)(e.target.value)}
          aria-label="Search entries"
        />
        <select
          value={kind}
          onChange={(e) => onFilter(setKind)(e.target.value as EntryKind | "")}
          aria-label="Kind"
        >
          <option value="">Income & expense</option>
          {KINDS.map((k) => (
            <option key={k} value={k}>
              {label(k)}
            </option>
          ))}
        </select>
        <select
          value={status}
          onChange={(e) => onFilter(setStatus)(e.target.value as EntryStatus | "")}
          aria-label="Status"
        >
          <option value="">Paid & planned</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {label(s)}
            </option>
          ))}
        </select>
        <select
          value={category}
          onChange={(e) => onFilter(setCategory)(e.target.value as Category | "")}
          aria-label="Type"
        >
          <option value="">Any type</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {label(c)}
            </option>
          ))}
        </select>
        <select
          value={period}
          onChange={(e) => onFilter(setPeriod)(e.target.value as Period | "")}
          aria-label="Period"
        >
          <option value="">Any period</option>
          {PERIODS.map((p) => (
            <option key={p} value={p}>
              {label(p)}
            </option>
          ))}
        </select>
        <label className="inline-label">
          From
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => onFilter(setDateFrom)(e.target.value)}
          />
        </label>
        <label className="inline-label">
          To
          <input type="date" value={dateTo} onChange={(e) => onFilter(setDateTo)(e.target.value)} />
        </label>
        <div className="push-right toolbar-buttons">
          <a className="button ghost" href={api.exportCsvUrl(filters)} download>
            Export CSV
          </a>
          <button type="button" className="primary" onClick={() => setEditing("new")}>
            + New entry
          </button>
        </div>
      </div>

      <ErrorNote error={entries.error ?? pay.error ?? repeat.error ?? remove.error} />
      {entries.isPending ? (
        <Spinner />
      ) : entries.data && entries.data.items.length > 0 ? (
        <>
          <ul className="list">
            {entries.data.items.map((entry) => (
              <FinanceItem
                key={entry.id}
                entry={entry}
                currency={currency}
                onPay={(e) => pay.mutate(e.id)}
                onEdit={setEditing}
                onRepeat={(e) => repeat.mutate(e.id)}
                onDelete={handleDelete}
              />
            ))}
          </ul>
          <Pagination
            total={entries.data.total}
            limit={LIMIT}
            offset={offset}
            onChange={setOffset}
          />
        </>
      ) : (
        <Empty>No entries match. Add an expense, income or upcoming bill.</Empty>
      )}

      <Modal
        open={editing !== null}
        title={editing === "new" ? "New finance entry" : "Edit entry"}
        onClose={() => setEditing(null)}
      >
        <FinanceForm
          initial={editing && editing !== "new" ? editing : undefined}
          currency={currency}
          onSubmit={handleSave}
          onCancel={() => setEditing(null)}
        />
      </Modal>
    </section>
  );
}
