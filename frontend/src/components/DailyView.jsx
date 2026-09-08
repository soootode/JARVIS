// src/components/DailyView.jsx
import { useState, useEffect, useCallback } from 'react';
<<<<<<< HEAD
import { CheckCircle2, Circle, Send, ClipboardList, Plus, Clock, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { apiFetch } from '../lib/apiClient';


// ── Toast component ──────────────────────────────────────────────────────────
const Toast = ({ message, type = 'success', onDismiss }) => (
  <motion.div
    initial={{ opacity: 0, y: 40, scale: 0.95 }}
    animate={{ opacity: 1, y: 0, scale: 1 }}
    exit={{ opacity: 0, y: 40, scale: 0.95 }}
    className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 px-5 py-2.5 rounded-full border text-sm backdrop-blur-sm shadow-lg shadow-black/40 ${
      type === 'success'
        ? 'border-emerald-400/40 text-emerald-100 bg-zinc-900/90'
        : 'border-red-400/50 text-red-300 bg-zinc-900/90'
    }`}
    onClick={onDismiss}
=======
import { CheckCircle2, Circle, Send } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = 'http://localhost:8000';

// ── Toast component (جایگزین alert) ──────────────────────────────────────────
const Toast = ({ message, type = 'success', onDismiss }) => (
  <motion.div
    initial={{ opacity: 0, y: 40 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: 40 }}
    className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 px-5 py-3 rounded-xl shadow-lg text-white text-sm font-medium ${
      type === 'success' ? 'bg-green-500' : 'bg-red-500'
    }`}
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
  >
    {message}
  </motion.div>
);

<<<<<<< HEAD
// تسک‌ها از بک‌اند با پسوند «(ساعت ۱۰:۰۰)» می‌آیند؛ ساعت را برای چیپ جدا می‌کنیم.
const extractTimeChip = (text) => {
  const match = text.match(/[（(]ساعت\s*([^)）]+)[)）]/);
  return match ? match[1].trim() : null;
};

const stripTimeChip = (text) => text.replace(/\s*[（(]ساعت\s*[^)）]+[)）]\s*/g, '').trim();

const TaskRow = ({ task, onToggle }) => {
  // ساعت از خود اسلات می‌آید (task.id = ساعت قفل‌شده)؛ اگر متن قدیمی
  // هنوز «(ساعت …)» داشت، همان ترجیح داده می‌شود.
  const time = extractTimeChip(task.text)
    || (Number.isInteger(task.id) && task.id >= 0 && task.id <= 23
      ? `${String(task.id).padStart(2, '0')}:00`
      : null);
  const label = stripTimeChip(task.text);

  return (
    <motion.button
      layout
      type="button"
      onClick={() => onToggle(task.id)}
      whileTap={{ scale: 0.98 }}
      transition={{ type: 'spring', stiffness: 500, damping: 35 }}
      className={`group flex items-center gap-3 w-full text-right p-3 rounded-md border cursor-pointer transition-colors ${
        task.completed
          ? 'border-zinc-800/60 bg-white/[0.02]'
          : 'border-zinc-800 hover:border-zinc-600 bg-transparent'
      }`}
    >
      <span className="relative flex-shrink-0">
        <AnimatePresence mode="wait" initial={false}>
          {task.completed ? (
            <motion.span
              key="done"
              initial={{ scale: 0.4, opacity: 0, rotate: -30 }}
              animate={{ scale: 1, opacity: 1, rotate: 0 }}
              exit={{ scale: 0.4, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 500, damping: 25 }}
              className="block"
            >
              <CheckCircle2 className="text-emerald-400" size={18} />
            </motion.span>
          ) : (
            <motion.span
              key="open"
              initial={{ scale: 0.6, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.6, opacity: 0 }}
              className="block"
            >
              <Circle className="text-white/30 group-hover:text-white/60 transition-colors" size={18} />
            </motion.span>
          )}
        </AnimatePresence>
      </span>

      <span
        className={`flex-1 text-sm transition-all duration-200 ${
          task.completed ? 'line-through text-white/30' : 'text-white/85'
        }`}
      >
        {label}
      </span>

      {time && (
        <span className="flex-shrink-0 inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-zinc-700 text-[11px] text-white/50 tabular-nums">
          <Clock size={11} />
          {time}
        </span>
      )}

      {task.completed && (
        <span className="flex-shrink-0 text-[10px] px-2 py-0.5 rounded-full bg-emerald-400/10 border border-emerald-400/30 text-emerald-300">
          انجام شد
        </span>
      )}
    </motion.button>
  );
};

=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
const DailyView = () => {
  const [tasks, setTasks] = useState([]);
  const [feedback, setFeedback] = useState('');
  const [loading, setLoading] = useState(true);
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
<<<<<<< HEAD
  const [newTaskText, setNewTaskText] = useState('');
  const [addingTask, setAddingTask] = useState(false);
=======
  // FIX: جایگزین alert() با toast state
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

<<<<<<< HEAD
  const fetchTasks = useCallback(async () => {
    try {
      const res = await apiFetch(`/api/daily/tasks`);
=======
  // ── بارگذاری تودوها از بک‌اند ────────────────────────────────────────────
  const fetchTasks = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/daily/tasks`);
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
      if (!res.ok) throw new Error('خطا در دریافت تودوها');
      const data = await res.json();
      setTasks(data.tasks || []);
    } catch (err) {
      console.error('fetchTasks error:', err);
      setTasks([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

<<<<<<< HEAD
=======
  // ── تغییر وضعیت تیک تودو ─────────────────────────────────────────────────
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
  const toggleTask = async (id) => {
    const task = tasks.find((t) => t.id === id);
    if (!task) return;

    const newCompleted = !task.completed;
    setTasks((prev) =>
      prev.map((t) => (t.id === id ? { ...t, completed: newCompleted } : t))
    );

    try {
<<<<<<< HEAD
      const res = await apiFetch(`/api/daily/tasks/${id}`, {
=======
      const res = await fetch(`${API_BASE}/api/daily/tasks/${id}`, {
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_text: task.text, completed: newCompleted }),
      });
      if (!res.ok) throw new Error('خطا در به‌روزرسانی');
    } catch (err) {
      console.error('toggleTask error:', err);
      setTasks((prev) =>
        prev.map((t) => (t.id === id ? { ...t, completed: !newCompleted } : t))
      );
<<<<<<< HEAD
      showToast('خطا در ثبت وضعیت تسک', 'error');
    }
  };

  const handleAddTask = async (e) => {
    e.preventDefault();
    const text = newTaskText.trim();
    if (!text || addingTask) return;
    setAddingTask(true);
    try {
      const res = await apiFetch(`/api/daily/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error('خطا در افزودن تسک');
      const data = await res.json();
      if (data.task) {
        setTasks((prev) => [...prev, data.task]);
      } else {
        await fetchTasks();
      }
      setNewTaskText('');
    } catch (err) {
      console.error('addTask error:', err);
      showToast('خطا در افزودن تسک', 'error');
    } finally {
      setAddingTask(false);
    }
  };

=======
    }
  };

  // ── ثبت فیدبک ────────────────────────────────────────────────────────────
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
  const handleSubmitFeedback = async () => {
    if (!feedback.trim()) return;
    setSubmittingFeedback(true);
    try {
<<<<<<< HEAD
      const res = await apiFetch(`/api/daily/feedback`, {
=======
      const res = await fetch(`${API_BASE}/api/daily/feedback`, {
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feedback: feedback.trim() }),
      });
      if (!res.ok) throw new Error('خطا در ثبت فیدبک');
<<<<<<< HEAD
=======
      // FIX: جایگزین alert() با toast
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
      showToast('فیدبک روزانه شما ثبت شد ✓');
      setFeedback('');
    } catch (err) {
      console.error('submitFeedback error:', err);
      showToast('خطا در ثبت فیدبک. دوباره تلاش کنید.', 'error');
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const completedCount = tasks.filter((t) => t.completed).length;
  const progress = tasks.length > 0 ? (completedCount / tasks.length) * 100 : 0;

  if (loading) {
    return (
<<<<<<< HEAD
      <div className="p-6 h-full flex items-center justify-center bg-zinc-950">
        <Loader2 size={20} className="text-white/30 animate-spin" />
=======
      <div className="p-6 h-full flex items-center justify-center">
        <div className="text-slate-400 text-sm">در حال بارگذاری...</div>
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
      </div>
    );
  }

  return (
<<<<<<< HEAD
    <div className="p-4 sm:p-6 space-y-5 sm:space-y-6 h-full overflow-y-auto scrollbar-hide bg-zinc-950">
      {/* Progress */}
      <motion.div layout className="border border-zinc-800 rounded-xl p-4 sm:p-5">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-sm text-white/75">پیشرفت امروز</h3>
          <span className="text-xs text-white/50 tabular-nums">
            {completedCount.toLocaleString('fa-IR')} از {tasks.length.toLocaleString('fa-IR')}
            {tasks.length > 0 && <span className="text-white/30 mr-1">({Math.round(progress).toLocaleString('fa-IR')}٪)</span>}
          </span>
        </div>
        <div className="w-full bg-white/[0.07] h-1.5 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            className="h-full rounded-full bg-gradient-to-l from-indigo-400 to-emerald-400"
          />
        </div>
      </motion.div>

      {/* Tasks + Feedback */}
      <div className="grid md:grid-cols-2 gap-5 sm:gap-6 items-start">
        {/* Tasks */}
        <motion.div layout className="border border-zinc-800 rounded-xl p-4 sm:p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm text-white/75">وظایف امروز</h3>
            {tasks.length > 0 && (
              <span className="text-[11px] text-white/30 tabular-nums">
                {tasks.length.toLocaleString('fa-IR')} تسک
              </span>
            )}
          </div>

          {/* Quick add */}
          <form onSubmit={handleAddTask} className="flex gap-2 mb-4">
            <input
              value={newTaskText}
              onChange={(e) => setNewTaskText(e.target.value)}
              placeholder="تسک سریع جدید..."
              maxLength={200}
              className="flex-1 min-w-0 bg-transparent border border-zinc-800 focus:border-white/40 rounded-md outline-none text-sm text-white placeholder-white/25 px-3 py-2 transition-colors"
            />
            <button
              type="submit"
              disabled={addingTask || !newTaskText.trim()}
              className="flex-shrink-0 inline-flex items-center justify-center w-9 h-9 rounded-md border border-zinc-700 text-white/70 hover:text-white hover:border-white/50 active:scale-95 disabled:opacity-35 disabled:cursor-not-allowed transition-all"
              aria-label="افزودن تسک"
            >
              {addingTask ? <Loader2 size={15} className="animate-spin" /> : <Plus size={16} />}
            </button>
          </form>

          <div className="space-y-2">
            {tasks.length === 0 ? (
              <div className="flex flex-col items-center gap-3 text-center py-10 text-white/35 text-sm">
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="w-14 h-14 rounded-2xl border border-dashed border-zinc-700 flex items-center justify-center"
                >
                  <ClipboardList size={22} className="text-white/25" />
                </motion.div>
                <div className="leading-relaxed">
                  هنوز وظیفه‌ای برای امروز تعریف نشده.
                  <br />
                  <span className="text-xs text-white/30">
                    یکی از راه‌های بالا اضافه کنید، یا با جارویس صحبت کنید تا برنامه‌تان ساخته شود.
                  </span>
                </div>
              </div>
            ) : (
              <AnimatePresence initial={false}>
                {tasks.map((task) => (
                  <TaskRow key={task.id} task={task} onToggle={toggleTask} />
                ))}
              </AnimatePresence>
            )}
          </div>
        </motion.div>

        {/* Feedback */}
        <motion.div layout className="border border-zinc-800 rounded-xl p-4 sm:p-5">
          <h3 className="text-sm text-white/75 mb-4">فیدبک و بازخورد روزانه</h3>
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="امروز چطور بود؟ چه چیزی یاد گرفتید؟ چه چالش‌هایی داشتید؟"
            maxLength={2000}
            className="w-full h-28 bg-transparent border border-zinc-800 focus:border-white/45 rounded-md outline-none text-sm text-white placeholder-white/25 p-3 resize-none transition-colors"
          />
          <div className="flex items-center justify-between mt-1 mb-3">
            <span className="text-[10px] text-white/20 tabular-nums">
              {feedback.length.toLocaleString('fa-IR')} / ۲۰۰۰
            </span>
          </div>
          <button
            onClick={handleSubmitFeedback}
            disabled={submittingFeedback || !feedback.trim()}
            className="relative mt-1 w-full py-2.5 group disabled:opacity-40 disabled:cursor-not-allowed active:scale-[0.99] transition-transform"
          >
            <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 200 44" preserveAspectRatio="none" style={{ overflow: 'visible' }}>
              <path
                d="M 3 5 C 60 3, 140 6, 197 4 C 199 15, 198 28, 197 39 C 140 41, 60 40, 3 41 C 1 28, 2 15, 3 5 Z"
                fill="none" stroke="#ffffff" strokeWidth="1.4"
                className="transition-all duration-200 group-hover:stroke-[1.8]"
              />
            </svg>
            <span className="relative z-10 flex items-center justify-center gap-2 text-sm text-white">
              {submittingFeedback ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
              {submittingFeedback ? 'در حال ثبت...' : 'ثبت فیدبک'}
            </span>
          </button>
        </motion.div>
      </div>

      {/* Toast */}
      <AnimatePresence>
        {toast && <Toast message={toast.message} type={toast.type} onDismiss={() => setToast(null)} />}
=======
    <div className="p-6 space-y-6 h-full overflow-y-auto scrollbar-hide">
      {/* Progress Bar */}
      <div className="bg-white rounded-2xl p-5 shadow-lg">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-lg font-bold text-slate-700">پیشرفت امروز</h3>
          <span className="text-sm font-semibold text-purple-600">
            {completedCount} از {tasks.length}
          </span>
        </div>
        <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5 }}
            className="h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full"
          />
        </div>
      </div>

      {/* Tasks Section */}
      <div className="bg-white rounded-2xl p-5 shadow-lg">
        <h3 className="text-lg font-bold text-slate-700 mb-4">وظایف امروز</h3>
        <div className="space-y-3">
          {tasks.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-sm">
              هنوز وظیفه‌ای برای امروز تعریف نشده.<br />
              <span className="text-xs">با جارویس صحبت کنید تا برنامه روزانه‌تان ساخته شود.</span>
            </div>
          ) : (
            tasks.map((task) => (
            <motion.div
              key={task.id}
              whileHover={{ scale: 1.02 }}
              onClick={() => toggleTask(task.id)}
              className={`flex items-center gap-3 p-4 rounded-xl cursor-pointer transition-all ${
                task.completed
                  ? 'bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200'
                  : 'bg-slate-50 border border-slate-200 hover:border-purple-300'
              }`}
            >
              {task.completed ? (
                <CheckCircle2 className="text-green-500 flex-shrink-0" size={24} />
              ) : (
                <Circle className="text-slate-400 flex-shrink-0" size={24} />
              )}
              <span className={`text-sm ${task.completed ? 'line-through text-slate-500' : 'text-slate-700'}`}>
                {task.text}
              </span>
            </motion.div>
            ))
          )}
        </div>
      </div>

      {/* Feedback Section */}
      <div className="bg-white rounded-2xl p-5 shadow-lg">
        <h3 className="text-lg font-bold text-slate-700 mb-4">فیدبک و بازخورد روزانه</h3>
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="امروز چطور بود؟ چه چیزی یاد گرفتید؟ چه چالش‌هایی داشتید؟"
          className="w-full h-32 px-4 py-3 rounded-xl bg-slate-50 text-slate-700 placeholder-slate-400 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
        />
        <button
          onClick={handleSubmitFeedback}
          disabled={submittingFeedback || !feedback.trim()}
          className="mt-3 w-full px-5 py-3 bg-gradient-to-br from-purple-500 to-blue-500 text-white rounded-xl font-semibold hover:shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <Send size={20} />
          <span>{submittingFeedback ? 'در حال ثبت...' : 'ثبت فیدبک'}</span>
        </button>
      </div>

      {/* FIX: Toast notification (جایگزین alert) */}
      <AnimatePresence>
        {toast && <Toast message={toast.message} type={toast.type} />}
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
      </AnimatePresence>
    </div>
  );
};

export default DailyView;
