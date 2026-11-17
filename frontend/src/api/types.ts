// TypeScript mirrors of the backend's Pydantic schemas (backend/app/schemas/).
// Keep the two in sync: if a field changes there, change it here.

export type Period = "daily" | "monthly" | "yearly";
export type Priority = "high" | "medium" | "low";
export type Category = "home" | "office" | "self" | "misc";
export type EntryKind = "expense" | "income";
export type EntryStatus = "planned" | "paid";

/** Money travels as a decimal string ("199.99") so no float ever touches it. */
export type Money = string;
/** Calendar date as "YYYY-MM-DD". */
export type ISODate = string;

export interface User {
  id: number;
  email: string;
  name: string;
  monthly_budget: Money | null;
  email_reminders: boolean;
  created_at: string;
  currency: string;
}

export interface RegisterInput {
  email: string;
  password: string;
  name: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface UserUpdate {
  name?: string;
  monthly_budget?: Money | null;
  email_reminders?: boolean;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface Todo {
  id: number;
  title: string;
  description: string | null;
  period: Period;
  priority: Priority;
  category: Category;
  due_date: ISODate | null;
  completed: boolean;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TodoInput {
  title: string;
  description: string | null;
  period: Period;
  priority: Priority;
  category: Category;
  due_date: ISODate | null;
}

export interface TodoQuery {
  period?: Period;
  priority?: Priority;
  category?: Category;
  completed?: boolean;
  due_from?: ISODate;
  due_to?: ISODate;
  q?: string;
  sort?: "due_date" | "priority" | "created_at" | "title";
  order?: "asc" | "desc";
  limit?: number;
  offset?: number;
}

export interface FinanceEntry {
  id: number;
  title: string;
  description: string | null;
  period: Period;
  priority: Priority;
  category: Category;
  kind: EntryKind;
  amount: Money;
  entry_date: ISODate;
  status: EntryStatus;
  created_at: string;
  updated_at: string;
}

export interface FinanceInput {
  title: string;
  description: string | null;
  period: Period;
  priority: Priority;
  category: Category;
  kind: EntryKind;
  amount: Money;
  entry_date: ISODate;
  status: EntryStatus;
}

export interface FinanceFilters {
  period?: Period;
  priority?: Priority;
  category?: Category;
  kind?: EntryKind;
  status?: EntryStatus;
  date_from?: ISODate;
  date_to?: ISODate;
  q?: string;
  sort?: "entry_date" | "amount" | "priority" | "created_at";
  order?: "asc" | "desc";
}

export interface FinanceQuery extends FinanceFilters {
  limit?: number;
  offset?: number;
}

export interface CategoryTotal {
  category: Category;
  income: Money;
  expense: Money;
}

export interface MonthTotal {
  month: string;
  income: Money;
  expense: Money;
  net: Money;
}

export interface FinanceStats {
  date_from: ISODate;
  date_to: ISODate;
  currency: string;
  total_income: Money;
  total_expense: Money;
  net: Money;
  by_category: CategoryTotal[];
  by_month: MonthTotal[];
}

export interface MonthSummary {
  month: string;
  income: Money;
  expense: Money;
  net: Money;
  budget: Money | null;
  budget_remaining: Money | null;
  budget_used_percent: number | null;
}

export interface HomeData {
  today: ISODate;
  currency: string;
  urgent_todos: Todo[];
  month: MonthSummary;
  upcoming_payments: FinanceEntry[];
  counts: { open_todos: number; overdue_todos: number; completed_this_week: number };
}

export interface Reminders {
  today: ISODate;
  overdue_todos: Todo[];
  due_today_todos: Todo[];
  upcoming_todos: Todo[];
  overdue_payments: FinanceEntry[];
  due_today_payments: FinanceEntry[];
  upcoming_payments: FinanceEntry[];
}
