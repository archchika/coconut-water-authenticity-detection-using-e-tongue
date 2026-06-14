/**
 * Phase 6.5 — Admin login: username/password → POST /api/auth/token/, store token.
 */
import { useState } from "react";
import { login, getApiErrorMessage } from "../api/client";
import { useAuth } from "../contexts/AuthContext";

export default function AdminLoginForm() {
  const { setToken } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { token } = await login(username, password);
      setToken(token);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: 320 }}>
      <h2 style={{ marginBottom: "1rem" }}>Admin login</h2>
      {error && (
        <p style={{ color: "#c53030", marginBottom: "0.5rem" }}>{error}</p>
      )}
      <div style={{ marginBottom: "0.75rem" }}>
        <label style={{ display: "block", marginBottom: "0.25rem" }}>
          Username
        </label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          autoComplete="username"
          style={{ width: "100%", padding: "0.5rem" }}
        />
      </div>
      <div style={{ marginBottom: "1rem" }}>
        <label style={{ display: "block", marginBottom: "0.25rem" }}>
          Password
        </label>
        <div style={{ position: "relative", display: "flex", alignItems: "center", gap: "0.25rem" }}>
          <input
            type={showPassword ? "text" : "password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            style={{ flex: 1, padding: "0.5rem", paddingRight: "2.5rem" }}
          />
          <button
            type="button"
            className="admin-password-toggle"
            onClick={() => setShowPassword((p) => !p)}
            title={showPassword ? "Hide password" : "Show password"}
            tabIndex={-1}
            style={{ color: "#166534" }}
          >
            {showPassword ? (
              /* Password visible: eye-slash = click to hide */
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#166534" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                <line x1="1" y1="1" x2="23" y2="23" />
              </svg>
            ) : (
              /* Password hidden: open eye = click to show */
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#166534" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            )}
          </button>
        </div>
      </div>
      <div style={{ display: "flex", justifyContent: "center" }}>
        <button type="submit" disabled={loading} style={{ padding: "0.5rem 1rem" }}>
          {loading ? "Logging in…" : "Log in"}
        </button>
      </div>
    </form>
  );
}
