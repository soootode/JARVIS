// src/components/ProtectedRoute.jsx
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// اگر لاگین نیست → /login
// اگر لاگین است ولی onboarding را تمام نکرده → /onboarding (مگر خودِ صفحه onboarding باشد)
// وگرنه → children را نشان بده
const ProtectedRoute = ({ requireOnboarding = true }) => {
  const { user, loading, isAuthenticated } = useAuth();

  if (loading) {
    return (
      <div
        className="h-screen w-screen flex items-center justify-center bg-[#0a0a0b]"
        style={{ fontFamily: "'IBM Plex Sans Arabic', sans-serif" }}
      >
        <div className="text-white/40 text-sm">در حال بررسی ورود...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requireOnboarding && user && !user.onboarding_completed) {
    return <Navigate to="/onboarding" replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;
