import { useState, useEffect, useCallback } from "react";
import { Outlet, Link, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import AdminLoginForm from "../components/AdminLoginForm";
import { fetchPredictions } from "../api/client";
import { format } from "date-fns";

/**
 * Phase 6.1 / 6.5 — Admin layout. Full side control view: fixed sidebar + main content.
 * No scrolled view; sidebar always visible.
 */
const SIDE_NAV = [
  { path: "/admin", label: "Home" },
  { path: "/admin/readings", label: "Sensor readings" },
  { path: "/admin/predictions", label: "Predictions" },
  { path: "/admin/logs", label: "Defects", showBadge: true },
];

export default function AdminLayout() {
  const { isAuthenticated, logout } = useAuth();
  const location = useLocation();
  const [defectCount, setDefectCount] = useState(0);

  const loadDefectCount = useCallback(async () => {
    try {
      const today = format(new Date(), "yyyy-MM-dd");
      const data = await fetchPredictions({
        date_from: today,
        date_to: today,
        status: "adulterated",
        limit: 999,
      });
      setDefectCount(data.length);
    } catch {
      setDefectCount(0);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      loadDefectCount();
    }
  }, [isAuthenticated, loadDefectCount, location.pathname]);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  };

  if (!isAuthenticated) {
    return (
      <main className="admin-layout admin-layout-login" onDoubleClick={toggleFullscreen} title="Double-click to toggle fullscreen">
        <img src="/company-logo.png" alt="Ceylon Coco" className="admin-login-bg-logo" />
        <div className="admin-login-wrap">
          <AdminLoginForm />
        </div>
      </main>
    );
  }

  return (
    <main className="admin-layout admin-layout-side">
      <aside className="admin-sidebar">
        <div className="admin-sidebar-header">
          <div className="admin-sidebar-actions">
            <Link to="/" className="admin-sidebar-link" style={{ textDecoration: "none" }}>
              View Public
            </Link>
            <button type="button" onClick={logout} className="admin-sidebar-btn">
              Log out
            </button>
          </div>
        </div>
        <nav className="admin-sidebar-nav">
          {SIDE_NAV.map(({ path, label, showBadge }) => (
            <Link
              key={path}
              to={path}
              className={`admin-sidebar-nav-item ${location.pathname === path ? "active" : ""}`}
              style={{ textDecoration: "none" }}
            >
              <span className="admin-sidebar-nav-label">{label}</span>
              {showBadge && defectCount > 0 && location.pathname !== "/admin/logs" && (
                <span className="admin-sidebar-badge" aria-label={`${defectCount} defect${defectCount !== 1 ? "s" : ""}`}>
                  {defectCount > 99 ? "99+" : defectCount}
                </span>
              )}
            </Link>
          ))}
        </nav>
      </aside>
      <div className="admin-main" onDoubleClick={toggleFullscreen} title="Double-click to toggle fullscreen">
        <Outlet />
      </div>
    </main>
  );
}
