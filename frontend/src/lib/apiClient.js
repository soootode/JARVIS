// src/lib/apiClient.js
// ─────────────────────────────────────────────────────────────────────────
// یک fetch wrapper مرکزی: base URL از env می‌آید، توکن JWT خودکار به هر
// request اضافه می‌شود، و 401 (توکن نامعتبر/منقضی) خودکار کاربر را
// logout و به /login هدایت می‌کند.
//
// همه‌ی کامپوننت‌ها (ChatView, DailyView, WeeklyView, PomodoroView,
// NotificationPoller) به‌جای fetch مستقیم باید از این استفاده کنند:
//     import { apiFetch } from '../lib/apiClient';
//     const res = await apiFetch('/api/daily/tasks');
// ─────────────────────────────────────────────────────────────────────────

// FIX (Failed to fetch): .env قبلاً VITE_API_BASE_URL تعریف می‌کرد ولی اینجا
// فقط VITE_API_BASE خوانده می‌شد — نتیجه‌اش fallback به localhost:8000 بود و
// فرانتِ دیپلوی‌شده «Failed to fetch» می‌گرفت. الان هر دو نام پشتیبانی می‌شوند.
export const API_BASE =
  import.meta.env.VITE_API_BASE ||
  import.meta.env.VITE_API_BASE_URL ||
  'http://localhost:8000';

const TOKEN_KEY = 'jarvis_token';

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

// وقتی توکن نامعتبر بشه (401)، این callback صدا زده می‌شه.
// AuthContext آن را روی logout ست می‌کند تا کل اپ از یک نقطه هماهنگ بشه.
let onUnauthorized = () => {
  window.location.href = '/login';
};

export function setUnauthorizedHandler(fn) {
  onUnauthorized = fn;
}

/**
 * fetch با base URL + هدر Authorization خودکار.
 * path باید با '/' شروع بشه، مثل '/api/daily/tasks'.
 */
export async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = {
    ...(options.body ? { 'Content-Type': 'application/json' } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch (err) {
    // خطای شبکه/CORS خام مرورگر («Failed to fetch») به پیام قابل‌فهم تبدیل می‌شود
    throw new Error('اتصال به سرور برقرار نشد. لطفاً اتصال اینترنت را بررسی کنید.');
  }

  if (res.status === 401) {
    setToken(null);
    onUnauthorized();
    throw new Error('Unauthorized');
  }

  return res;
}

/** میانبر برای endpointهایی که همیشه JSON برمی‌گردانند و باید ok باشند. */
export async function apiJson(path, options = {}) {
  const res = await apiFetch(path, options);
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch { /* ignore */ }
    throw new Error(detail);
  }
  return res.json();
}
