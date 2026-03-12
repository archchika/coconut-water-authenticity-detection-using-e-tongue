/**
 * Phase 6.5 — Simple auth for admin: token in localStorage, set on API client.
 */
import { createContext, useContext, useState, useCallback, useEffect } from "react";
import { setAuthToken } from "../api/client";

const STORAGE_KEY = "ceylon_coco_admin_token";

type AuthContextType = {
  token: string | null;
  setToken: (token: string | null) => void;
  logout: () => void;
  isAuthenticated: boolean;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(STORAGE_KEY);
  });

  useEffect(() => {
    setAuthToken(token);
  }, [token]);

  const setToken = useCallback((t: string | null) => {
    setTokenState(t);
    if (t) localStorage.setItem(STORAGE_KEY, t);
    else localStorage.removeItem(STORAGE_KEY);
  }, []);

  const logout = useCallback(() => setToken(null), [setToken]);

  return (
    <AuthContext.Provider
      value={{
        token,
        setToken,
        logout,
        isAuthenticated: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
