// src/AppShell.jsx
// بازطراحی کامل: پس‌زمینه مشکی، بدون کارت شناور، تب‌ها به‌جای دکمه‌های
// گرد رنگی حالا فقط متن با یه خط زیر تب فعال. منطق تب‌ها و auth دقیقاً
// همون قبلیه، فقط ظاهر عوض شده.
import { useState } from 'react';
import { MessageCircle, Calendar, CalendarDays, Wrench, Timer, LogOut } from 'lucide-react';
import { useAuth } from './context/AuthContext';
import RobotAvatar from './components/RobotAvatar';
import ChatView from './components/ChatView';
import DailyView from './components/DailyView';
import WeeklyView from './components/WeeklyView';
import NotificationPoller from './components/NotificationPoller';
import PomodoroView from './components/PomodoroView';

const FONT_LINK_ID = 'jarvis-sketch-font';
const useSketchFont = () => {
  if (typeof document === 'undefined') return;
  if (document.getElementById(FONT_LINK_ID)) return;
  const link = document.createElement('link');
  link.id = FONT_LINK_ID;
  link.rel = 'stylesheet';
  link.href = 'https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800&display=swap';
  document.head.appendChild(link);
};

function AppShell() {
  useSketchFont();
  const [activeTab, setActiveTab] = useState('chat');
  const { user, logout } = useAuth();

  const tabs = [
    { id: 'chat', label: 'چت با جارویس', icon: MessageCircle },
    { id: 'daily', label: 'برنامه و فیدبک روزانه', icon: Calendar },
    { id: 'weekly', label: 'برنامه هفتگی', icon: CalendarDays },
    { id: 'pomodoro', label: 'پومودورو', icon: Timer },
    { id: 'dev', label: 'بخش توسعه', icon: Wrench, disabled: true },
  ];

  const ActiveComponent = { chat: ChatView, daily: DailyView, weekly: WeeklyView, pomodoro: PomodoroView }[activeTab];

  return (
    <div
      className="min-h-screen h-screen flex flex-col bg-zinc-950 text-white"
      dir="rtl"
      style={{ fontFamily: "'Vazirmatn', sans-serif" }}
    >
      {/* Header */}
      <header className="flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4 border-b border-zinc-800 flex-shrink-0">
        <div className="flex items-center gap-3">
          <RobotAvatar emotionalState="happy" size="small" />
          <div>
            <p className="text-sm">{user?.display_name || 'جارویس'}</p>
            <p className="text-xs text-white/35">
              {user?.display_name ? 'دستیار هوشمند شخصی شما' : 'دستیار هوشمند شخصی شما'}
            </p>
          </div>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-1.5 text-xs text-white/40 hover:text-white transition-colors"
        >
          <LogOut size={14} />
          خروج
        </button>
      </header>

      {/* Tabs */}
      <nav className="flex gap-1 px-4 pt-3 border-b border-zinc-800 flex-shrink-0 overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              onClick={() => !tab.disabled && setActiveTab(tab.id)}
              disabled={tab.disabled}
              className={`relative flex items-center gap-2 px-4 py-2.5 text-xs whitespace-nowrap transition-colors ${
                isActive
                  ? 'text-white'
                  : tab.disabled
                    ? 'text-white/20 cursor-not-allowed'
                    : 'text-white/45 hover:text-white/80'
              }`}
            >
              <Icon size={15} />
              <span className="hidden sm:inline">{tab.label}</span>
              {isActive && <span className="absolute -bottom-px right-0 left-0 h-[1.5px] bg-white" />}
            </button>
          );
        })}
      </nav>

      {/* Active view */}
      <main className="flex-1 overflow-hidden">
        <ActiveComponent />
      </main>

      <NotificationPoller />
    </div>
  );
}

export default AppShell;
