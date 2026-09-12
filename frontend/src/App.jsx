// src/App.jsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import VerifyEmailPage from './pages/VerifyEmailPage';
import OnboardingWizard from './pages/OnboardingWizard';
import AppShell from './AppShell'; // چیزی که قبلاً کل UI اصلی (Chat/Daily/Weekly/Pomodoro tabs) رو نگه می‌داشت

// صفحات عمومی (landing/login/signup) اگر کاربر از قبل لاگین باشد،
// مستقیم به داخل اپ هدایتش می‌کنند.
const PublicOnly = ({ children }) => {
  const { isAuthenticated, loading, user } = useAuth();
  if (loading) return null;
  if (isAuthenticated) {
    return <Navigate to={user?.onboarding_completed ? '/app' : '/onboarding'} replace />;
  }
  return children;
};

const AppRoutes = () => (
  <Routes>
    <Route path="/" element={<PublicOnly><LandingPage /></PublicOnly>} />
    <Route path="/login" element={<PublicOnly><LoginPage /></PublicOnly>} />
    <Route path="/signup" element={<PublicOnly><SignupPage /></PublicOnly>} />
    <Route path="/forgot-password" element={<PublicOnly><ForgotPasswordPage /></PublicOnly>} />
    <Route path="/reset-password" element={<PublicOnly><ResetPasswordPage /></PublicOnly>} />
    <Route path="/verify-email" element={<VerifyEmailPage />} />

    {/* onboarding: باید لاگین باشد ولی لازم نیست onboarding را قبلاً تمام کرده باشد */}
    <Route element={<ProtectedRoute requireOnboarding={false} />}>
      <Route path="/onboarding" element={<OnboardingWizard />} />
    </Route>

    {/* اپ اصلی: باید لاگین باشد و onboarding را تمام کرده باشد */}
    <Route element={<ProtectedRoute requireOnboarding />}>
      <Route path="/app/*" element={<AppShell />} />
    </Route>

    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
);

const App = () => (
  <BrowserRouter>
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  </BrowserRouter>
);

export default App;
