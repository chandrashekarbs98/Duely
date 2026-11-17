import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../../api/client";
import type { Category, Period, Priority, Todo, TodoInput, TodoQuery } from "../../api/types";
import { Empty, ErrorNote, Modal, Pagination, Spinner, useDebounced } from "../../components/ui";
import { CATEGORIES, PERIODS, PRIORITIES, label } from "../../lib/labels";
import { useDataMutation } from "../../lib/queries";
import TodoForm from "./TodoForm";
import TodoItem from "./TodoItem";

const LIMIT = 20;
type StatusFilter = "open" | "done" | "all";

export default function TodosTab() {
  const [search, setSearch] = useState("");
  const [period, setPeriod] = useState<Period | "">("");
  const [priority, setPriority] = useState<Priority | "">("");
  const [category, setCategory] = useState<Category | "">("");
  const [status, setStatus] = useState<StatusFilter>("open");
  const [sort, setSort] = useState<NonNullable<TodoQuery["sort"]>>("due_date");
  const [offset, setOffset] = useState(0);
  const [editing, setEditing] = useState<Todo | "new" | null>(null);

  const q = useDebounced(search.trim());
  const query: TodoQuery = {
    q: q || undefined,
    period: period || undefined,
    priority: priority || undefined,
    category: category || undefined,
    completed: status === "all" ? undefined : status === "done",
    sort,
    limit: LIMIT,
    offset,
  };

  // The query key includes every filter, so each combination is cached separately.
  const todos = useQuery({
    queryKey: ["todos", query],
    queryFn: () => api.listTodos(query),
    placeholderData: keepPreviousData, // keep showing the old page while the new one loads
  });

  const create = useDataMutation((data: TodoInput) => api.createTodo(data));
  const update = useDataMutation(({ id, data }: { id: number; data: TodoInput }) =>
    api.updateTodo(id, data),
  );
  const toggle = useDataMutation((id: number) => api.toggleTodo(id));
  const repeat = useDataMutation((id: number) => api.repeatTodo(id));
  const remove = useDataMutation((id: number) => api.deleteTodo(id));

  function resetPage<T>(setter: (v: T) => void) {
    return (value: T) => {
      setter(value);
      setOffset(0);
    };
  }

  async function handleSave(data: TodoInput) {
    if (editing === "new") await create.mutateAsync(data);
    else if (editing) await update.mutateAsync({ id: editing.id, data });
    setEditing(null);
  }

  function handleDelete(todo: Todo) {
    if (window.confirm(`Delete "${todo.title}"? This cannot be undone.`)) remove.mutate(todo.id);
  }

  const mutationError = toggle.error ?? repeat.error ?? remove.error;

  return (
    <section aria-label="To-dos">
      <div className="toolbar">
        <input
          type="search"
          placeholder="Search to-dos…"
          value={search}
          onChange={(e) => resetPage(setSearch)(e.target.value)}
          aria-label="Search to-dos"
        />
        <select
          value={status}
          onChange={(e) => resetPage(setStatus)(e.target.value as StatusFilter)}
          aria-label="Status"
        >
          <option value="open">Open</option>
          <option value="done">Completed</option>
          <option value="all">All</option>
        </select>
        <select
          value={period}
          onChange={(e) => resetPage(setPeriod)(e.target.value as Period | "")}
          aria-label="Period"
        >
          <option value="">Any period</option>
          {PERIODS.map((p) => (
            <option key={p} value={p}>
              {label(p)}
            </option>
          ))}
        </select>
        <select
          value={priority}
          onChange={(e) => resetPage(setPriority)(e.target.value as Priority | "")}
          aria-label="Priority"
        >
          <option value="">Any priority</option>
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>
              {label(p)}
            </option>
          ))}
        </select>
        <select
          value={category}
          onChange={(e) => resetPage(setCategory)(e.target.value as Category | "")}
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
          value={sort}
          onChange={(e) => setSort(e.target.value as NonNullable<TodoQuery["sort"]>)}
          aria-label="Sort by"
        >
          <option value="due_date">Sort: due date</option>
          <option value="priority">Sort: priority</option>
          <option value="created_at">Sort: newest</option>
          <option value="title">Sort: title</option>
        </select>
        <button type="button" className="primary push-right" onClick={() => setEditing("new")}>
          + New to-do
        </button>
      </div>

      <ErrorNote error={todos.error ?? mutationError} />
      {todos.isPending ? (
        <Spinner />
      ) : todos.data && todos.data.items.length > 0 ? (
        <>
          <ul className="list">
            {todos.data.items.map((todo) => (
              <TodoItem
                key={todo.id}
                todo={todo}
                onToggle={(t) => toggle.mutate(t.id)}
                onEdit={setEditing}
                onRepeat={(t) => repeat.mutate(t.id)}
                onDelete={handleDelete}
              />
            ))}
          </ul>
          <Pagination total={todos.data.total} limit={LIMIT} offset={offset} onChange={setOffset} />
        </>
      ) : (
        <Empty>No to-dos match. Add one with “New to-do”.</Empty>
      )}

      <Modal
        open={editing !== null}
        title={editing === "new" ? "New to-do" : "Edit to-do"}
        onClose={() => setEditing(null)}
      >
        <TodoForm
          initial={editing && editing !== "new" ? editing : undefined}
          onSubmit={handleSave}
          onCancel={() => setEditing(null)}
        />
      </Modal>
    </section>
  );
}
