import { Outlet, Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import AdminLoginForm from "../components/AdminLoginForm";

/**
 * Phase 6.1 / 6.5 — Admin layout. Protected: show login if not authenticated.
 * Header includes link to Public Dashboard.
 */
export default function AdminLayout() {
  const { isAuthenticated, logout } = useAuth();

  if (!isAuthenticated) {
    return (
      <main className="admin-layout">
        <div style={{ maxWidth: 1400, margin: "0 auto", padding: "1rem" }}>
          <AdminLoginForm />
        </div>
      </main>
    );
  }

  return (
    <main className="admin-layout">
      <div style={{ maxWidth: 1400, margin: "0 auto", padding: "1rem" }}>
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: "0.75rem", marginBottom: "1rem" }}>
          <h1 style={{ margin: 0 }}>Admin Dashboard</h1>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Link to="/" className="admin-header-btn admin-header-link" style={{ textDecoration: "none" }}>
              View Public Dashboard
            </Link>
            <button type="button" onClick={logout} className="admin-header-btn">
              Log out
            </button>
          </div>
        </div>
        <Outlet />
      </div>
    </main>
  );
}
