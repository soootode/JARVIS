// src/context/AuthContext.jsx
import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiJson, getToken, setToken, setUnauthorizedHandler } from '../lib/apiClient';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);       // { id, email, display_name, onboarding_completed }
  const [loading, setLoading] = useState(true);  // در حال بررسی توکن اولیه

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  // اگر یک request هرجای اپ 401 بگیره، همینجا logout می‌کنیم
  useEffect(() => {
    setUnauthorizedHandler(logout);
  }, [logout]);

  // بارگذاری اولیه: اگر توکن ذخیره‌شده معتبره، پروفایل رو بگیر
  useEffect(() => {
    (async () => {
      const token = getToken();
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const me = await apiJson('/api/auth/me');
        setUser(me);
      } catch {
        setToken(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const login = async (email, password) => {
    const data = await apiJson('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    setToken(data.access_token);
    setUser({
      id: data.user_id,
      email: data.email,
      display_name: data.display_name,
      onboarding_completed: data.onboarding_completed,
    });
    return data;
  };

  const signup = async (email, password, displayName) => {
    const data = await apiJson('/api/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password, display_name: displayName }),
    });
    setToken(data.access_token);
    setUser({
      id: data.user_id,
      email: data.email,
      display_name: data.display_name,
      onboarding_completed: data.onboarding_completed,
    });
    return data;
  };

  const markOnboardingComplete = () => {
    setUser((prev) => (prev ? { ...prev, onboarding_completed: true } : prev));
  };

  return (
    <AuthContext.Provider
      value={{ user, loading, login, signup, logout, markOnboardingComplete, isAuthenticated: !!user }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth باید داخل AuthProvider استفاده بشه');
  return ctx;
};
