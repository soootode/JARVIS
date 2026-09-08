// src/pages/ResetPasswordPage.jsx
import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { apiJson } from '../lib/apiClient';
import SketchButton from '../components/ui/SketchButton';
import { SketchInput } from '../components/ui/SketchInput';

const ResetPasswordPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';

  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!token) {
      setError('لینک بازیابی نامعتبر است. توکنی پیدا نشد.');
    }
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (password.length < 8) {
      setError('رمز عبور باید حداقل ۸ کاراکتر باشد.');
      return;
    }
    if (password !== confirm) {
      setError('تکرار رمز عبور مطابقت ندارد.');
      return;
    }
    setLoading(true);
    try {
      await apiJson('/api/auth/reset-password', {
        method: 'POST',
        body: JSON.stringify({ token, new_password: password }),
      });
      setDone(true);
      setTimeout(() => navigate('/login', { replace: true }), 2500);
    } catch (err) {
      setError(err.message || 'تغییر رمز عبور ناموفق بود.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center bg-zinc-950 text-white px-4"
      dir="rtl"
      style={{ fontFamily: "'IBM Plex Sans Arabic', sans-serif" }}
    >
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-medium text-center mb-10">رمز عبور جدید</h1>

        {done ? (
          <div className="text-center space-y-6">
            <p className="text-sm text-emerald-400">✅ رمز عبور با موفقیت تغییر کرد.</p>
            <Link to="/login" className="inline-block text-sm text-white hover:underline">
              ورود به حساب
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-xs text-white/60 font-medium mb-1.5">رمز عبور جدید</label>
              <SketchInput
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="حداقل ۸ کاراکتر"
              />
            </div>
            <div>
              <label className="block text-xs text-white/60 font-medium mb-1.5">تکرار رمز عبور جدید</label>
              <SketchInput
                type="password"
                required
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                placeholder="••••••••"
              />
            </div>

            {error && <p className="text-sm text-red-400">{error}</p>}

            <div className="pt-4 flex justify-center">
              <SketchButton type="submit" variant="filled" disabled={loading || !token}>
                {loading ? 'در حال تغییر...' : 'ثبت رمز جدید'}
              </SketchButton>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default ResetPasswordPage;
