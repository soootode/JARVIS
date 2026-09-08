// src/components/PomodoroView.jsx
import { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Square, RotateCcw, Coffee, Brain, Plus, Minus } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { apiFetch } from '../lib/apiClient';


// ── Toast ──────────────────────────────────────────────────────────
const Toast = ({ message, type = 'success' }) => (
  <motion.div
    initial={{ opacity: 0, y: 40 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: 40 }}
    className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 px-5 py-3 border text-sm bg-zinc-950 ${
      type === 'success' ? 'border-white/70 text-white' : 'border-red-400 text-red-400'
    }`}
  >
    {message}
  </motion.div>
);

// ── Circular progress ring ─────────────────────────────────────────
const TimerRing = ({ progress, color, children }) => {
  const r = 90;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - Math.max(0, Math.min(1, progress)));
  return (
    <div className="relative flex items-center justify-center" style={{ width: 220, height: 220 }}>
      <svg width="220" height="220" className="absolute -rotate-90">
        <circle cx="110" cy="110" r={r} stroke="rgba(255,255,255,0.12)" strokeWidth="1.5" fill="none" />
        <motion.circle
          cx="110" cy="110" r={r}
          stroke="#ffffff"
          strokeWidth="1.5"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circ}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.5 }}
        />
      </svg>
      <div className="relative z-10 flex flex-col items-center justify-center">
        {children}
      </div>
    </div>
  );
};

// ── Pomodoro dots ──────────────────────────────────────────────────
const PomodoroDots = ({ total, done }) => (
  <div className="flex gap-2 justify-center flex-wrap">
    {Array.from({ length: total }).map((_, i) => (
      <motion.div
        key={i}
        initial={{ scale: 0.8 }}
        animate={{ scale: i < done ? 1.1 : 1 }}
        className={`w-3.5 h-3.5 rounded-full border transition-all ${
          i < done ? 'bg-white border-white' : 'bg-transparent border-white/30'
        }`}
      />
    ))}
  </div>
);

// ── SESSION TYPES ──────────────────────────────────────────────────
const SESSION_TYPES = {
  focus:       { label: 'تمرکز',           minutes: 25, icon: Brain },
  short_break: { label: 'استراحت کوتاه',   minutes: 5,  icon: Coffee },
  long_break:  { label: 'استراحت طولانی',  minutes: 15, icon: Coffee },
};

// ── MAIN ───────────────────────────────────────────────────────────
const PomodoroView = () => {
  const [sessionType, setSessionType]     = useState('focus');
  const [activeSession, setActiveSession] = useState(null);
  const [timeLeft, setTimeLeft]           = useState(null);
  const [dailyTasks, setDailyTasks]       = useState([]);
  const [selectedTask, setSelectedTask]   = useState(null);  // { id, text, completed }
  // تعداد پومودوروهای موردنیاز برای هر تسک (ذخیره local)
  const [pomodoroNeeds, setPomodoroNeeds] = useState({});    // { taskId: count }
  // تعداد پومودوروهای انجام‌شده در این session برای تسک انتخابی
  const [doneForTask, setDoneForTask]     = useState({});    // { taskId: count }
  const [toast, setToast]                 = useState(null);
  const [loading, setLoading]             = useState(false);
  const intervalRef                       = useRef(null);

  const cfg = SESSION_TYPES[sessionType];

  const showToast = (msg, type = 'success') => {
    setToast({ message: msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  // ── بارگذاری تسک‌های روزانه ────────────────────────────────────────
  const fetchDailyTasks = useCallback(async () => {
    try {
      const res = await apiFetch(`/api/daily/tasks`);
      if (!res.ok) return;
      const data = await res.json();
      setDailyTasks(data.tasks || []);
    } catch (e) {
      console.error('fetchDailyTasks error:', e);
    }
  }, []);

  // ── بارگذاری سشن فعال از بک‌اند ───────────────────────────────────
  const fetchActiveSession = useCallback(async () => {
    try {
      const res = await apiFetch(`/api/pomodoro/active`);
      if (!res.ok) return;
      const data = await res.json();
      if (data.active_session) {
        const s = data.active_session;
        setActiveSession(s);
        setSessionType(s.session_type);
        const endTime = new Date(s.end_time).getTime();
        const remaining = Math.max(0, Math.floor((endTime - Date.now()) / 1000));
        setTimeLeft(remaining);
      }
    } catch (e) {
      console.error('fetchActiveSession error:', e);
    }
  }, []);

  useEffect(() => {
    fetchDailyTasks();
    fetchActiveSession();
  }, [fetchDailyTasks, fetchActiveSession]);

  // ── تایمر countdown ────────────────────────────────────────────────
  useEffect(() => {
    clearInterval(intervalRef.current);
    if (!activeSession || timeLeft === null || timeLeft <= 0) return;

    intervalRef.current = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          clearInterval(intervalRef.current);
          handleTimerEnd();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(intervalRef.current);
  }, [activeSession]);

  // ── وقتی تایمر تمام شد ─────────────────────────────────────────────
  const handleTimerEnd = async () => {
    // سشن رو سمت سرور هم ببند تا ردیف PomodoroSession وضعیت completed
    // بگیره و پومودورو به WorkTask مربوطه کرِدیت بشه.
    if (activeSession) {
      try {
        await apiFetch(`/api/pomodoro/stop/${activeSession.id}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ completed: true }),
        });
      } catch (e) {
        console.error('auto-stop session error:', e);
      }
    }

    if (!selectedTask || sessionType !== 'focus') {
      showToast('⏰ زمان تمام شد!');
      setActiveSession(null);
      setTimeLeft(null);
      return;
    }

    const taskId = selectedTask.id;
    const need   = pomodoroNeeds[taskId] || 1;
    const done   = (doneForTask[taskId] || 0) + 1;

    setDoneForTask(prev => ({ ...prev, [taskId]: done }));

    if (done >= need) {
      // همه پومودوروها تمام شد → تسک رو تیک بزن
      showToast(`✅ تسک "${selectedTask.text}" تکمیل شد!`);
      await tickTask(taskId);
      setDailyTasks(prev =>
        prev.map(t => t.id === taskId ? { ...t, completed: true } : t)
      );
      setSelectedTask(prev => prev ? { ...prev, completed: true } : prev);
    } else {
      showToast(`🍅 پومودورو ${done} از ${need} تمام شد! یه استراحت کوتاه بگیر.`);
    }

    setActiveSession(null);
    setTimeLeft(null);
  };

  // ── تیک زدن تسک روزانه ─────────────────────────────────────────────
  const tickTask = async (taskId) => {
    try {
      const task = dailyTasks.find(t => t.id === taskId);
      if (!task) return;
      await apiFetch(`/api/daily/tasks/${taskId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_text: task.text, completed: true }),
      });
    } catch (e) {
      console.error('tickTask error:', e);
    }
  };

  // ── شروع سشن ───────────────────────────────────────────────────────
  const handleStart = async () => {
    setLoading(true);
    try {
      const res = await apiFetch(`/api/pomodoro/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: null,
          duration_minutes: cfg.minutes,
          session_type: sessionType,
        }),
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setActiveSession(data.session);
      setTimeLeft(cfg.minutes * 60);
    } catch {
      showToast('خطا در شروع پومودورو', 'error');
    } finally {
      setLoading(false);
    }
  };

  // ── توقف سشن ───────────────────────────────────────────────────────
  const handleStop = async () => {
    if (!activeSession) return;
    clearInterval(intervalRef.current);
    setLoading(true);
    try {
      await apiFetch(`/api/pomodoro/stop/${activeSession.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ completed: false }),
      });
      showToast('سشن متوقف شد.');
    } catch { /* silent */ }
    setActiveSession(null);
    setTimeLeft(null);
    setLoading(false);
  };

  // ── format time ────────────────────────────────────────────────────
  const formatTime = (secs) => {
    const total = secs !== null ? secs : cfg.minutes * 60;
    const m = Math.floor(total / 60);
    const s = total % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };

  const totalSecs = cfg.minutes * 60;
  const progress  = timeLeft !== null ? timeLeft / totalSecs : 1;
  const isRunning = !!activeSession;

  const activeTasks    = dailyTasks.filter(t => !t.completed);
  const completedTasks = dailyTasks.filter(t => t.completed);

  return (
    <div className="p-6 space-y-5 h-full overflow-y-auto scrollbar-hide bg-zinc-950">

      {/* Session type selector */}
      <div className="border border-white/15 rounded-lg p-4">
        <div className="flex gap-2 justify-center flex-wrap">
          {Object.entries(SESSION_TYPES).map(([type, c]) => {
            const Icon = c.icon;
            return (
              <button
                key={type}
                disabled={isRunning}
                onClick={() => { setSessionType(type); setTimeLeft(null); }}
                className={`flex items-center gap-2 px-4 py-2 text-xs transition-all border
                  ${sessionType === type
                    ? 'border-white text-white'
                    : 'border-white/15 text-white/40 hover:text-white/70'
                  } disabled:opacity-40 disabled:cursor-not-allowed`}
              >
                <Icon size={14} />
                {c.label} ({c.minutes}m)
              </button>
            );
          })}
        </div>
      </div>

      {/* Timer */}
      <div className="border border-white/15 rounded-lg p-6 flex flex-col items-center gap-5">
        <TimerRing progress={progress}>
          <span className="text-5xl font-light text-white tabular-nums">
            {formatTime(timeLeft)}
          </span>
          <span className="text-xs text-white/40 mt-1">{cfg.label}</span>
        </TimerRing>

        {/* نمایش پومودوروهای تسک انتخابی */}
        {selectedTask && sessionType === 'focus' && (
          <div className="flex flex-col items-center gap-2 w-full">
            <p className="text-sm text-white/50 text-center">
              تسک: <span className="text-white">{selectedTask.text}</span>
            </p>
            <PomodoroDots
              total={pomodoroNeeds[selectedTask.id] || 1}
              done={doneForTask[selectedTask.id] || 0}
            />
          </div>
        )}

        {/* Controls */}
        <div className="flex items-center gap-4">
          {!isRunning ? (
            <button
              onClick={handleStart}
              disabled={loading}
              className="relative px-8 py-3 group disabled:opacity-40"
            >
              <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 160 50" preserveAspectRatio="none" style={{ overflow: 'visible' }}>
                <path
                  d="M 3 6 C 40 3, 100 7, 157 5 C 159 18, 158 32, 157 44 C 100 46, 40 45, 3 46 C 1 32, 2 18, 3 6 Z"
                  fill="#ffffff" stroke="#ffffff" strokeWidth="1.4"
                  className="transition-all duration-200 group-hover:stroke-[1.8]"
                />
              </svg>
              <span className="relative z-10 flex items-center gap-2 text-black font-medium text-sm">
                <Play size={16} fill="black" />
                شروع
              </span>
            </button>
          ) : (
            <button
              onClick={handleStop}
              disabled={loading}
              className="relative px-8 py-3 group disabled:opacity-40"
            >
              <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 160 50" preserveAspectRatio="none" style={{ overflow: 'visible' }}>
                <path
                  d="M 3 6 C 40 3, 100 7, 157 5 C 159 18, 158 32, 157 44 C 100 46, 40 45, 3 46 C 1 32, 2 18, 3 6 Z"
                  fill="none" stroke="#ef4444" strokeWidth="1.4"
                  className="transition-all duration-200 group-hover:stroke-[1.8]"
                />
              </svg>
              <span className="relative z-10 flex items-center gap-2 text-red-400 font-medium text-sm">
                <Square size={16} />
                توقف
              </span>
            </button>
          )}
          {!isRunning && timeLeft !== null && (
            <button
              onClick={() => setTimeLeft(null)}
              className="p-3 text-white/40 hover:text-white transition-all"
            >
              <RotateCcw size={18} />
            </button>
          )}
        </div>
      </div>

      {/* انتخاب تسک روزانه */}
      <div className="border border-white/15 rounded-lg p-5">
        <h3 className="text-sm text-white/70 mb-3">
          وظایف امروز
        </h3>

        {activeTasks.length === 0 && completedTasks.length === 0 ? (
          <p className="text-sm text-white/30 text-center py-4">
            هیچ وظیفه‌ای برای امروز ثبت نشده.<br/>
            <span className="text-xs">با جارویس صحبت کنید.</span>
          </p>
        ) : (
          <div className="space-y-2">
            {/* تسک‌های فعال */}
            {activeTasks.map(task => {
              const need = pomodoroNeeds[task.id] || 1;
              const done = doneForTask[task.id] || 0;
              const isSelected = selectedTask?.id === task.id;

              return (
                <motion.div
                  key={task.id}
                  onClick={() => !isRunning && setSelectedTask(isSelected ? null : task)}
                  className={`border rounded-md p-3 cursor-pointer transition-all ${
                    isSelected ? 'border-white' : 'border-white/15 hover:border-white/35'
                  } ${isRunning ? 'cursor-default' : ''}`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-sm text-white/80 text-right flex-1">{task.text}</span>

                    {/* تعداد پومودورو */}
                    {isSelected && (
                      <div
                        className="flex items-center gap-2 flex-shrink-0"
                        onClick={e => e.stopPropagation()}
                      >
                        <button
                          disabled={isRunning || need <= 1}
                          onClick={() => setPomodoroNeeds(prev => ({ ...prev, [task.id]: Math.max(1, need - 1) }))}
                          className="w-6 h-6 rounded border border-white/20 hover:border-white/50 flex items-center justify-center disabled:opacity-30 text-white"
                        >
                          <Minus size={12} />
                        </button>
                        <span className="text-sm text-white w-8 text-center">
                          {need}🍅
                        </span>
                        <button
                          disabled={isRunning || need >= 8}
                          onClick={() => setPomodoroNeeds(prev => ({ ...prev, [task.id]: Math.min(8, need + 1) }))}
                          className="w-6 h-6 rounded border border-white/20 hover:border-white/50 flex items-center justify-center disabled:opacity-30 text-white"
                        >
                          <Plus size={12} />
                        </button>
                      </div>
                    )}
                  </div>

                  {/* dots پیشرفت */}
                  {isSelected && need > 0 && (
                    <div className="mt-2">
                      <PomodoroDots total={need} done={done} />
                    </div>
                  )}
                </motion.div>
              );
            })}

            {/* تسک‌های تکمیل‌شده */}
            {completedTasks.length > 0 && (
              <div className="mt-3 pt-3 border-t border-white/10">
                <p className="text-xs text-white/30 mb-2 text-right">تکمیل‌شده</p>
                {completedTasks.map(task => (
                  <div
                    key={task.id}
                    className="border border-white/10 rounded-md p-3 mb-2 opacity-50"
                  >
                    <span className="text-sm text-white/50 line-through text-right block">
                      ✓ {task.text}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <AnimatePresence>
        {toast && <Toast message={toast.message} type={toast.type} />}
      </AnimatePresence>
    </div>
  );
};

export default PomodoroView;
