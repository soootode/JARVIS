// src/App.jsx
<<<<<<< HEAD
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
=======
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, Calendar, CalendarDays, Wrench, Timer } from 'lucide-react';
import RobotAvatar from './components/RobotAvatar';
import ChatView from './components/ChatView';
import DailyView from './components/DailyView';
import WeeklyView from './components/WeeklyView';
import NotificationPoller from './components/NotificationPoller';
import PomodoroView from './components/PomodoroView';


function App() {
  const [activeTab, setActiveTab] = useState('chat');

  const tabs = [
    { id: 'chat', label: 'چت با جارویس', icon: MessageCircle },
    { id: 'daily', label: 'برنامه و فیدبک روزانه', icon: Calendar },
    { id: 'weekly', label: 'برنامه هفتگی', icon: CalendarDays },
    { id: 'pomodoro', label: 'پومودورو', icon: Timer },
    { id: 'dev', label: 'بخش توسعه', icon: Wrench, disabled: true }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-600 via-purple-600 to-blue-500 p-4" dir="rtl">
      <div className="max-w-7xl mx-auto h-[calc(100vh-2rem)] flex flex-col">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/95 backdrop-blur-md rounded-2xl shadow-lg p-4 mb-4"
        >
          <div className="flex items-center justify-between flex-wrap gap-4">
            {/* Avatar & Title */}
            <div className="flex items-center gap-4">
              <div className="bg-gradient-to-br from-purple-100 to-blue-100 rounded-full p-2">
                <RobotAvatar emotionalState="happy" size="normal" />
              </div>
              <div>
                <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                  جارویس
                </h1>
                <p className="text-sm text-slate-600">دستیار هوشمند شخصی شما</p>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex gap-2 flex-wrap">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => !tab.disabled && setActiveTab(tab.id)}
                    disabled={tab.disabled}
                    className={`px-4 py-2.5 rounded-xl font-semibold transition-all flex items-center gap-2 text-sm ${
                      activeTab === tab.id
                        ? 'bg-gradient-to-br from-purple-500 to-blue-500 text-white shadow-lg scale-105'
                        : tab.disabled
                          ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    <Icon size={18} />
                    <span className="hidden sm:inline">{tab.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </motion.div>

        {/* Main Content */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex-1 bg-white/95 backdrop-blur-md rounded-2xl shadow-lg overflow-hidden"
        >
          <AnimatePresence mode="wait">
            {activeTab === 'chat' && (
              <motion.div
                key="chat"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="h-full"
              >
                <ChatView />
              </motion.div>
            )}
            {activeTab === 'daily' && (
              <motion.div
                key="daily"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="h-full"
              >
                <DailyView />
              </motion.div>
            )}
            {activeTab === 'weekly' && (
              <motion.div
                key="weekly"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="h-full"
              >
                <WeeklyView />
              </motion.div>
            )} 
            {activeTab === 'pomodoro' && (
              <motion.div
                key="pomodoro"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="h-full"
              >
                <PomodoroView />
              </motion.div>   
            )}

          </AnimatePresence>
        </motion.div>
      </div>
      <NotificationPoller />
    </div>
  );
}
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9

export default App;
