// src/pages/LoginPage.jsx
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import SketchButton from '../components/ui/SketchButton';
import { SketchInput } from '../components/ui/SketchInput';

const LoginPage = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await login(email.trim(), password);
      navigate(data.onboarding_completed ? '/app' : '/onboarding', { replace: true });
    } catch (err) {
      setError(err.message || 'ورود ناموفق بود.');
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
        <h1 className="text-2xl font-medium text-center mb-10">ورود به جارویس</h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-xs text-white/60 font-medium mb-1.5">ایمیل</label>
            <SketchInput
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-xs text-white/60 font-medium mb-1.5">رمز عبور</label>
            <SketchInput
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <div className="flex justify-center">
            <Link to="/forgot-password" className="text-xs text-white/45 hover:text-white/80 transition-colors">
              فراموشی رمز عبور؟
            </Link>
          </div>

          <div className="pt-4 flex justify-center">
            <SketchButton type="submit" variant="filled" disabled={loading}>
              {loading ? 'در حال ورود...' : 'ورود'}
            </SketchButton>
          </div>
        </form>

        <p className="text-center text-sm text-white/55 mt-10">
          حساب نداری؟{' '}
          <Link to="/signup" className="text-white hover:underline">
            ثبت‌نام کن
          </Link>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
