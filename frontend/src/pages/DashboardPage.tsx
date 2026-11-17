import { lazy, Suspense } from "react";
import { useSearchParams } from "react-router";
import { Spinner } from "../components/ui";
import FinanceList from "../features/finance/FinanceList";
import TodosTab from "../features/todos/TodosTab";

// Code splitting: the charts library is big, so it downloads only when Charts is opened.
const FinanceStats = lazy(() => import("../features/finance/FinanceStats"));

type Tab = "todos" | "finance";
type FinanceView = "list" | "stats";

/** Tabs live in the URL (?tab=finance&view=stats) so links and the back button work. */
export default function DashboardPage() {
  const [params, setParams] = useSearchParams();
  const tab: Tab = params.get("tab") === "finance" ? "finance" : "todos";
  const view: FinanceView = params.get("view") === "stats" ? "stats" : "list";

  function go(next: { tab: Tab; view?: FinanceView }) {
    const p = new URLSearchParams({ tab: next.tab });
    if (next.tab === "finance") p.set("view", next.view ?? "list");
    setParams(p);
  }

  return (
    <>
      <div className="page-header">
        <h1>Dashboard</h1>
      </div>
      <div className="tabs" role="tablist" aria-label="Dashboard sections">
        <button
          type="button"
          role="tab"
          aria-selected={tab === "todos"}
          className={tab === "todos" ? "active" : ""}
          onClick={() => go({ tab: "todos" })}
        >
          To-dos
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "finance"}
          className={tab === "finance" ? "active" : ""}
          onClick={() => go({ tab: "finance" })}
        >
          Finance
        </button>
      </div>

      {tab === "todos" ? (
        <TodosTab />
      ) : (
        <>
          <div className="subtabs" role="tablist" aria-label="Finance views">
            <button
              type="button"
              role="tab"
              aria-selected={view === "list"}
              className={view === "list" ? "active" : ""}
              onClick={() => go({ tab: "finance", view: "list" })}
            >
              Entries
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={view === "stats"}
              className={view === "stats" ? "active" : ""}
              onClick={() => go({ tab: "finance", view: "stats" })}
            >
              Charts & analysis
            </button>
          </div>
          {view === "list" ? (
            <FinanceList />
          ) : (
            <Suspense fallback={<Spinner />}>
              <FinanceStats />
            </Suspense>
          )}
        </>
      )}
    </>
  );
}
