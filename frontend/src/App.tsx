import { Link, Route, Routes } from "react-router";
import { PublicOnly, RequireAuth } from "./auth/RouteGuards";
import Layout from "./components/Layout";
import { LoginPage, RegisterPage } from "./pages/AuthPages";
import DashboardPage from "./pages/DashboardPage";
import HomePage from "./pages/HomePage";
import RemindersPage from "./pages/RemindersPage";
import SettingsPage from "./pages/SettingsPage";

function NotFound() {
  return (
    <div className="center-page">
      <h1>Page not found</h1>
      <Link to="/">Go home</Link>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<PublicOnly />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>
      <Route element={<RequireAuth />}>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/reminders" element={<RemindersPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
