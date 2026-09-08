// src/pages/VerifyEmailPage.jsx
import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { apiJson } from '../lib/apiClient';

const VerifyEmailPage = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const [status, setStatus] = useState('verifying'); // verifying | success | error
  const [message, setMessage] = useState('');
  const ranRef = useRef(false);

  useEffect(() => {
    if (ranRef.current) return;
    ranRef.current = true;

    if (!token) {
      setStatus('error');
      setMessage('توکنی برای تأیید پیدا نشد.');
      return;
    }

    apiJson('/api/auth/verify-email', {
      method: 'POST',
      body: JSON.stringify({ token }),
    })
      .then((data) => {
        setStatus('success');
        setMessage(data.message || 'ایمیل شما تأیید شد.');
      })
      .catch((err) => {
        setStatus('error');
        setMessage(err.message || 'تأیید ایمیل ناموفق بود.');
      });
  }, [token]);

  return (
    <div
      className="min-h-screen flex items-center justify-center bg-zinc-950 text-white px-4"
      dir="rtl"
      style={{ fontFamily: "'IBM Plex Sans Arabic', sans-serif" }}
    >
      <div className="w-full max-w-sm text-center space-y-6">
        <h1 className="text-2xl font-medium">تأیید ایمیل</h1>

        {status === 'verifying' && (
          <p className="text-sm text-white/60">در حال بررسی لینک تأیید...</p>
        )}

        {status === 'success' && (
          <>
            <p className="text-sm text-emerald-400">✅ {message}</p>
            <Link to="/login" className="inline-block text-sm text-white hover:underline">
              ورود به حساب
            </Link>
          </>
        )}

        {status === 'error' && (
          <>
            <p className="text-sm text-red-400">{message}</p>
            <Link to="/login" className="inline-block text-sm text-white hover:underline">
              بازگشت به ورود
            </Link>
          </>
        )}
      </div>
    </div>
  );
};

export default VerifyEmailPage;
