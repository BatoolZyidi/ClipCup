import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiUrl } from '../api';

const AuthContext = createContext(null);

const TOKEN_KEY = 'clipcup_access';
const REFRESH_KEY = 'clipcup_refresh';
const USER_KEY = 'clipcup_user';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem(USER_KEY)); } catch { return null; }
  });
  const [accessToken, setAccessToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [loading, setLoading] = useState(false);

  // Attach token to all API requests
  const authFetch = useCallback(async (url, options = {}) => {
    const token = localStorage.getItem(TOKEN_KEY);
    const headers = {
      ...(options.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    let res = await fetch(url, { ...options, headers });

    // Try refresh once if 401
    if (res.status === 401) {
      const refreshToken = localStorage.getItem(REFRESH_KEY);
      if (refreshToken) {
        const refreshRes = await fetch(apiUrl('/api/auth/refresh'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh: refreshToken }),
        });
        if (refreshRes.ok) {
          const { access } = await refreshRes.json();
          localStorage.setItem(TOKEN_KEY, access);
          setAccessToken(access);
          res = await fetch(url, {
            ...options,
            headers: { ...(options.headers || {}), Authorization: `Bearer ${access}` },
          });
        } else {
          logout();
        }
      }
    }
    return res;
  }, []);

  const login = useCallback(async (identifier, password) => {
    setLoading(true);
    try {
      const res = await fetch(apiUrl('/api/auth/login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username_or_email: identifier, password }),
      });
      let data = {};
      try {
        data = await res.json();
      } catch {
        throw new Error(
          res.status === 502 || res.status === 504 || res.status === 404
            ? 'Backend server is not running or unreachable (check port 8000).'
            : `Server returned status ${res.status}`
        );
      }
      if (!res.ok) throw new Error(data.error || 'Login failed');
      localStorage.setItem(TOKEN_KEY, data.access);
      localStorage.setItem(REFRESH_KEY, data.refresh);
      localStorage.setItem(USER_KEY, JSON.stringify(data.user));
      setAccessToken(data.access);
      setUser(data.user);
      return { ok: true };
    } catch (err) {
      return { ok: false, error: err.message };
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (fields) => {
    setLoading(true);
    try {
      const res = await fetch(apiUrl('/api/auth/register'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(fields),
      });
      let data = {};
      try {
        data = await res.json();
      } catch {
        throw new Error(
          res.status === 502 || res.status === 504 || res.status === 404
            ? 'Backend server is not running or unreachable on port 8000.'
            : `Server returned status ${res.status}`
        );
      }
      if (!res.ok) throw new Error(data.error || 'Registration failed');
      localStorage.setItem(TOKEN_KEY, data.access);
      localStorage.setItem(REFRESH_KEY, data.refresh);
      localStorage.setItem(USER_KEY, JSON.stringify(data.user));
      setAccessToken(data.access);
      setUser(data.user);
      return { ok: true };
    } catch (err) {
      return { ok: false, error: err.message };
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    const refreshToken = localStorage.getItem(REFRESH_KEY);
    if (refreshToken) {
      try {
        await fetch(apiUrl('/api/auth/logout'), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY)}`,
          },
          body: JSON.stringify({ refresh: refreshToken }),
        });
      } catch { /* ignore */ }
    }
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
    setAccessToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, accessToken, loading, login, register, logout, authFetch }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
