// src/pages/ForgotPasswordPage.jsx
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { apiJson } from '../lib/apiClient';
import SketchButton from '../components/ui/SketchButton';
import { SketchInput } from '../components/ui/SketchInput';

const ForgotPasswordPage = () => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await apiJson('/api/auth/forgot-password', {
        method: 'POST',
        body: JSON.stringify({ email: email.trim() }),
      });
      setSent(true);
    } catch (err) {
      setError(err.message || 'ارسال درخواست ناموفق بود.');
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
        <h1 className="text-2xl font-medium text-center mb-4">بازیابی رمز عبور</h1>

        {sent ? (
          <div className="text-center space-y-6 mt-8">
            <div className="w-14 h-14 mx-auto rounded-2xl border border-white/20 flex items-center justify-center text-2xl">
              📧
            </div>
            <p className="text-sm text-white/70 leading-relaxed">
              لینک بازیابی رمز به ایمیل شما ارسال شد.
              <br />
              <span className="text-xs text-white/40">لینک تا یک ساعت اعتبار دارد.</span>
            </p>
            <Link to="/login" className="inline-block text-sm text-white hover:underline">
              بازگشت به ورود
            </Link>
          </div>
        ) : (
          <>
            <p className="text-sm text-white/50 text-center mb-10 leading-relaxed">
              ایمیل حساب‌تان را وارد کنید تا لینک بازیابی رمز عبور برایتان ارسال شود.
            </p>

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

              {error && <p className="text-sm text-red-400">{error}</p>}

              <div className="pt-4 flex justify-center">
                <SketchButton type="submit" variant="filled" disabled={loading}>
                  {loading ? 'در حال ارسال...' : 'ارسال لینک بازیابی'}
                </SketchButton>
              </div>
            </form>

            <p className="text-center text-sm text-white/55 mt-10">
              یادت اومد؟{' '}
              <Link to="/login" className="text-white hover:underline">
                وارد شو
              </Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
