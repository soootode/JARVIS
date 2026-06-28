// src/components/PomodoroView.jsx
import { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Square, RotateCcw, Coffee, Brain, Plus, Minus } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = 'http://localhost:8000';

// ── Toast ─────────────────────────────────────────────────────────────────────
const Toast = ({ message, type = 'success' }) => (
  <motion.div
    initial={{ opacity: 0, y: 40 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: 40 }}
    className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 px-5 py-3 rounded-xl shadow-lg text-white text-sm font-medium ${
      type === 'success' ? 'bg-green-500' : 'bg-red-500'
    }`}
  >
    {message}
  </motion.div>
);

// ── Circular progress ring ────────────────────────────────────────────────────
const TimerRing = ({ progress, color, children }) => {
  const r = 90;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - Math.max(0, Math.min(1, progress)));
  return (
    <div className="relative flex items-center justify-center" style={{ width: 220, height: 220 }}>
      <svg width="220" height="220" className="absolute -rotate-90">
        <circle cx="110" cy="110" r={r} stroke="#e2e8f0" strokeWidth="10" fill="none" />
        <motion.circle
          cx="110" cy="110" r={r}
          stroke={color}
          strokeWidth="10"
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

// ── Pomodoro dots ─────────────────────────────────────────────────────────────
const PomodoroDots = ({ total, done }) => (
  <div className="flex gap-2 justify-center flex-wrap">
    {Array.from({ length: total }).map((_, i) => (
      <motion.div
        key={i}
        initial={{ scale: 0.8 }}
        animate={{ scale: i < done ? 1.1 : 1 }}
        className={`w-5 h-5 rounded-full border-2 transition-all ${
          i < done
            ? 'bg-gradient-to-br from-purple-500 to-blue-500 border-purple-500'
            : 'bg-white border-slate-300'
        }`}
      />
    ))}
  </div>
);

// ── SESSION TYPES ─────────────────────────────────────────────────────────────
const SESSION_TYPES = {
  focus:       { label: 'تمرکز',         minutes: 25, color: 'from-purple-500 to-blue-500',   icon: Brain,  ringColor: '#8b5cf6' },
  short_break: { label: 'استراحت کوتاه', minutes: 5,  color: 'from-green-400 to-emerald-500', icon: Coffee, ringColor: '#10b981' },
  long_break:  { label: 'استراحت بلند',  minutes: 15, color: 'from-blue-400 to-cyan-500',     icon: Coffee, ringColor: '#06b6d4' },
};

// ── MAIN ──────────────────────────────────────────────────────────────────────
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

  // ── بارگذاری تسک‌های روزانه ──────────────────────────────────────────────
  const fetchDailyTasks = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/daily/tasks`);
      if (!res.ok) return;
      const data = await res.json();
      setDailyTasks(data.tasks || []);
    } catch (e) {
      console.error('fetchDailyTasks error:', e);
    }
  }, []);

  // ── بارگذاری سشن فعال از بک‌اند ──────────────────────────────────────────
  const fetchActiveSession = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/pomodoro/active`);
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

  // ── تایمر countdown ────────────────────────────────────────────────────────
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

  // ── وقتی تایمر تموم شد ───────────────────────────────────────────────────
  const handleTimerEnd = async () => {
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
      // همه پومودوروها تموم شد → تسک رو تیک بزن
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

  // ── تیک زدن تسک روزانه ───────────────────────────────────────────────────
  const tickTask = async (taskId) => {
    try {
      const task = dailyTasks.find(t => t.id === taskId);
      if (!task) return;
      await fetch(`${API_BASE}/api/daily/tasks/${taskId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_text: task.text, completed: true }),
      });
    } catch (e) {
      console.error('tickTask error:', e);
    }
  };

  // ── شروع سشن ─────────────────────────────────────────────────────────────
  const handleStart = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/pomodoro/start`, {
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

  // ── توقف سشن ─────────────────────────────────────────────────────────────
  const handleStop = async () => {
    if (!activeSession) return;
    clearInterval(intervalRef.current);
    setLoading(true);
    try {
      await fetch(`${API_BASE}/api/pomodoro/stop/${activeSession.id}`, {
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

  // ── format time ──────────────────────────────────────────────────────────
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
    <div className="p-6 space-y-5 h-full overflow-y-auto scrollbar-hide">

      {/* Session type selector */}
      <div className="bg-white rounded-2xl p-4 shadow-lg">
        <div className="flex gap-2 justify-center flex-wrap">
          {Object.entries(SESSION_TYPES).map(([type, c]) => {
            const Icon = c.icon;
            return (
              <button
                key={type}
                disabled={isRunning}
                onClick={() => { setSessionType(type); setTimeLeft(null); }}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all
                  ${sessionType === type
                    ? `bg-gradient-to-br ${c.color} text-white shadow-md`
                    : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                <Icon size={16} />
                {c.label} ({c.minutes}m)
              </button>
            );
          })}
        </div>
      </div>

      {/* Timer */}
      <div className="bg-white rounded-2xl p-6 shadow-lg flex flex-col items-center gap-5">
        <TimerRing progress={progress} color={cfg.ringColor}>
          <span className="text-5xl font-mono font-bold text-slate-700 tabular-nums">
            {formatTime(timeLeft)}
          </span>
          <span className="text-sm text-slate-400 mt-1">{cfg.label}</span>
        </TimerRing>

        {/* نمایش پومودوروهای تسک انتخابی */}
        {selectedTask && sessionType === 'focus' && (
          <div className="flex flex-col items-center gap-2 w-full">
            <p className="text-sm text-slate-500 text-center">
              تسک: <span className="font-semibold text-slate-700">{selectedTask.text}</span>
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
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={handleStart}
              disabled={loading}
              className={`flex items-center gap-2 px-8 py-3 rounded-xl text-white font-bold text-base bg-gradient-to-br ${cfg.color} shadow-lg hover:shadow-xl transition-all disabled:opacity-50`}
            >
              <Play size={20} fill="white" />
              شروع
            </motion.button>
          ) : (
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={handleStop}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-3 rounded-xl text-white font-bold bg-red-500 hover:bg-red-600 shadow-lg transition-all disabled:opacity-50"
            >
              <Square size={18} fill="white" />
              توقف
            </motion.button>
          )}
          {!isRunning && timeLeft !== null && (
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={() => setTimeLeft(null)}
              className="p-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 transition-all"
            >
              <RotateCcw size={20} />
            </motion.button>
          )}
        </div>
      </div>

      {/* انتخاب تسک روزانه */}
      <div className="bg-white rounded-2xl p-5 shadow-lg">
        <h3 className="text-base font-bold text-slate-700 mb-3">
          وظایف امروز
        </h3>

        {activeTasks.length === 0 && completedTasks.length === 0 ? (
          <p className="text-sm text-slate-400 text-center py-4">
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
                  whileHover={{ scale: 1.01 }}
                  onClick={() => !isRunning && setSelectedTask(isSelected ? null : task)}
                  className={`rounded-xl border-2 p-3 cursor-pointer transition-all ${
                    isSelected
                      ? 'border-purple-400 bg-purple-50'
                      : 'border-slate-200 bg-slate-50 hover:border-purple-200'
                  } ${isRunning ? 'cursor-default' : ''}`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-sm text-slate-700 text-right flex-1">{task.text}</span>

                    {/* تعداد پومودورو */}
                    {isSelected && (
                      <div
                        className="flex items-center gap-2 flex-shrink-0"
                        onClick={e => e.stopPropagation()}
                      >
                        <button
                          disabled={isRunning || need <= 1}
                          onClick={() => setPomodoroNeeds(prev => ({ ...prev, [task.id]: Math.max(1, need - 1) }))}
                          className="w-6 h-6 rounded-full bg-slate-200 hover:bg-slate-300 flex items-center justify-center disabled:opacity-40"
                        >
                          <Minus size={12} />
                        </button>
                        <span className="text-sm font-bold text-purple-600 w-6 text-center">
                          {need}🍅
                        </span>
                        <button
                          disabled={isRunning || need >= 8}
                          onClick={() => setPomodoroNeeds(prev => ({ ...prev, [task.id]: Math.min(8, need + 1) }))}
                          className="w-6 h-6 rounded-full bg-slate-200 hover:bg-slate-300 flex items-center justify-center disabled:opacity-40"
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
              <div className="mt-3 pt-3 border-t border-slate-100">
                <p className="text-xs text-slate-400 mb-2 text-right">تکمیل‌شده</p>
                {completedTasks.map(task => (
                  <div
                    key={task.id}
                    className="rounded-xl border border-green-200 bg-green-50 p-3 mb-2 opacity-60"
                  >
                    <span className="text-sm text-slate-500 line-through text-right block">
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
