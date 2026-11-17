import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { api } from "../api/client";
import { useAuth, useUser } from "../auth/AuthProvider";
import { ErrorNote } from "../components/ui";
import { isValidMoneyInput } from "../lib/money";

export default function SettingsPage() {
  const user = useUser();
  const { setUser, logout } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState(user.name);
  const [budget, setBudget] = useState(user.monthly_budget ?? "");
  const [formError, setFormError] = useState<string | null>(null);
  const [confirmText, setConfirmText] = useState("");

  const save = useMutation({
    mutationFn: () =>
      api.updateMe({
        name: name.trim(),
        monthly_budget: budget.trim() === "" ? null : budget.trim(),
      }),
    onSuccess: setUser,
  });

  const remove = useMutation({
    mutationFn: api.deleteMe,
    onSuccess: async () => {
      await logout().catch(() => undefined);
      navigate("/register", { replace: true });
    },
  });

  function handleSave(event: FormEvent) {
    event.preventDefault();
    if (budget.trim() !== "" && !isValidMoneyInput(budget)) {
      setFormError("Budget must be a positive amount with at most 2 decimals, or empty.");
      return;
    }
    setFormError(null);
    save.mutate();
  }

  return (
    <>
      <div className="page-header">
        <h1>Settings</h1>
      </div>
      <div className="stack narrow">
        <section className="card" aria-labelledby="profile-title">
          <h2 id="profile-title">Profile & budget</h2>
          <form className="form" onSubmit={handleSave}>
            <label>
              Email
              <input value={user.email} disabled />
            </label>
            <label>
              Name
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                maxLength={100}
              />
            </label>
            <label>
              Monthly budget ({user.currency}) <span className="muted">(leave empty for none)</span>
              <input
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                inputMode="decimal"
                placeholder="e.g. 40000"
              />
            </label>
            {formError && (
              <p className="error-note" role="alert">
                {formError}
              </p>
            )}
            <ErrorNote error={save.error} />
            <div className="form-actions start">
              <button type="submit" className="primary" disabled={save.isPending}>
                {save.isPending ? "Saving…" : "Save"}
              </button>
              {save.isSuccess && (
                <span className="success" role="status">
                  Saved
                </span>
              )}
            </div>
          </form>
        </section>

        <section className="card danger-zone" aria-labelledby="danger-title">
          <h2 id="danger-title">Delete account</h2>
          <p className="muted">
            Permanently deletes your account, to-dos and finance entries. This cannot be undone.
          </p>
          <label>
            Type <strong>DELETE</strong> to confirm
            <input value={confirmText} onChange={(e) => setConfirmText(e.target.value)} />
          </label>
          <ErrorNote error={remove.error} />
          <div className="form-actions start">
            <button
              type="button"
              className="danger-button"
              disabled={confirmText !== "DELETE" || remove.isPending}
              onClick={() => remove.mutate()}
            >
              Delete my account
            </button>
          </div>
        </section>
      </div>
    </>
  );
}
