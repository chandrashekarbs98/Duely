import { Navigate, Outlet, useLocation } from "react-router";
import { useAuth } from "./AuthProvider";

function FullPageSpinner() {
  return (
    <div className="center-page" role="status" aria-live="polite">
      Loading…
    </div>
  );
}

/** Wraps pages that need a logged-in user. Remembers where you were going. */
export function RequireAuth() {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <FullPageSpinner />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <Outlet />;
}

/** Login/Register: if you're already logged in, go home. */
export function PublicOnly() {
  const { user, loading } = useAuth();
  if (loading) return <FullPageSpinner />;
  if (user) return <Navigate to="/" replace />;
  return <Outlet />;
}
