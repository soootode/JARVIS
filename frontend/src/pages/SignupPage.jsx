// src/pages/SignupPage.jsx
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import SketchButton from '../components/ui/SketchButton';
import { SketchInput } from '../components/ui/SketchInput';

const SignupPage = () => {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (password.length < 8) {
      setError('رمز عبور باید حداقل ۸ کاراکتر باشد.');
      return;
    }
    setLoading(true);
    try {
      await signup(email.trim(), password, displayName.trim() || undefined);
      navigate('/onboarding', { replace: true });
    } catch (err) {
      setError(err.message || 'ثبت‌نام ناموفق بود.');
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
        <h1 className="text-2xl font-medium text-center mb-10">ساخت حساب جارویس</h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-xs text-white/60 font-medium mb-1.5">اسم (اختیاری)</label>
            <SketchInput
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="اسمی که جارویس صدات کنه"
            />
          </div>
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
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="حداقل ۸ کاراکتر"
            />
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <div className="pt-4 flex justify-center">
            <SketchButton type="submit" variant="filled" disabled={loading}>
              {loading ? 'در حال ساخت حساب...' : 'ثبت‌نام'}
            </SketchButton>
          </div>
        </form>

        <p className="text-center text-sm text-white/55 mt-10">
          حساب داری؟{' '}
          <Link to="/login" className="text-white hover:underline">
            وارد شو
          </Link>
        </p>
      </div>
    </div>
  );
};

export default SignupPage;
