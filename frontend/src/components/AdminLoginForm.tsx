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
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="current-password"
          style={{ width: "100%", padding: "0.5rem" }}
        />
      </div>
      <button type="submit" disabled={loading} style={{ padding: "0.5rem 1rem" }}>
        {loading ? "Logging in…" : "Log in"}
      </button>
    </form>
  );
}
