// The one typed API client. Every backend call goes through `request`.
// Paths are relative ("/api/..."): in dev Vite proxies them to the backend; in production
// FastAPI serves this app and the API from the same origin.

import type {
  FinanceEntry,
  FinanceFilters,
  FinanceInput,
  FinanceQuery,
  FinanceStats,
  HomeData,
  ISODate,
  LoginInput,
  Page,
  RegisterInput,
  Reminders,
  Todo,
  TodoInput,
  TodoQuery,
  User,
  UserUpdate,
} from "./types";

export class ApiError extends Error {
  readonly status: number;
  readonly detail: unknown;

  constructor(status: number, detail: unknown) {
    super(describeDetail(status, detail));
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

/** FastAPI sends `detail` as a string, or (for 422) a list of `{ loc, msg }` objects. */
function describeDetail(status: number, detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first: unknown = detail[0];
    if (first !== null && typeof first === "object" && "msg" in first) {
      const msg = String(first.msg).replace(/^Value error, /, "");
      const loc = "loc" in first && Array.isArray(first.loc) ? first.loc.at(-1) : undefined;
      return loc !== undefined && typeof loc === "string" ? `${loc}: ${msg}` : msg;
    }
  }
  return `Request failed with status ${status}`;
}

type QueryValue = string | number | boolean | undefined | null;

/** Build "?a=1&b=x", skipping empty values so the backend sees only real filters. */
export function toQueryString(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, QueryValue][]) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...init,
    credentials: "include", // send the httpOnly auth cookie
    headers: { "Content-Type": "application/json", ...init.headers },
  });

  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    const detail =
      body !== null && typeof body === "object" && "detail" in body ? body.detail : body;
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

const json = (body: unknown): RequestInit => ({ body: JSON.stringify(body) });

export const api = {
  health: () => request<{ status: string; database: string }>("/api/health"),

  // auth
  me: () => request<User>("/api/auth/me"),
  register: (data: RegisterInput) =>
    request<User>("/api/auth/register", { method: "POST", ...json(data) }),
  login: (data: LoginInput) => request<User>("/api/auth/login", { method: "POST", ...json(data) }),
  logout: () => request<undefined>("/api/auth/logout", { method: "POST" }),
  updateMe: (data: UserUpdate) => request<User>("/api/auth/me", { method: "PATCH", ...json(data) }),
  deleteMe: () => request<undefined>("/api/auth/me", { method: "DELETE" }),

  // todos
  listTodos: (query: TodoQuery) => request<Page<Todo>>(`/api/todos${toQueryString(query)}`),
  createTodo: (data: TodoInput) => request<Todo>("/api/todos", { method: "POST", ...json(data) }),
  updateTodo: (id: number, data: TodoInput) =>
    request<Todo>(`/api/todos/${id}`, { method: "PUT", ...json(data) }),
  toggleTodo: (id: number) => request<Todo>(`/api/todos/${id}/toggle`, { method: "PATCH" }),
  repeatTodo: (id: number) => request<Todo>(`/api/todos/${id}/repeat`, { method: "POST" }),
  deleteTodo: (id: number) => request<undefined>(`/api/todos/${id}`, { method: "DELETE" }),

  // finances
  listFinances: (query: FinanceQuery) =>
    request<Page<FinanceEntry>>(`/api/finances${toQueryString(query)}`),
  createFinance: (data: FinanceInput) =>
    request<FinanceEntry>("/api/finances", { method: "POST", ...json(data) }),
  updateFinance: (id: number, data: FinanceInput) =>
    request<FinanceEntry>(`/api/finances/${id}`, { method: "PUT", ...json(data) }),
  payFinance: (id: number) => request<FinanceEntry>(`/api/finances/${id}/pay`, { method: "PATCH" }),
  repeatFinance: (id: number) =>
    request<FinanceEntry>(`/api/finances/${id}/repeat`, { method: "POST" }),
  deleteFinance: (id: number) => request<undefined>(`/api/finances/${id}`, { method: "DELETE" }),
  financeStats: (range: { date_from?: ISODate; date_to?: ISODate }) =>
    request<FinanceStats>(`/api/finances/stats${toQueryString(range)}`),
  /** A plain link: the browser downloads the file and sends the cookie itself. */
  exportCsvUrl: (filters: FinanceFilters) => `/api/finances/export.csv${toQueryString(filters)}`,

  // dashboard
  home: () => request<HomeData>("/api/home"),
  reminders: () => request<Reminders>("/api/reminders"),
  sendTestEmail: () =>
    request<{ sent_to: string }>("/api/reminders/test-email", { method: "POST" }),
};
