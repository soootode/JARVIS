// src/components/DailyView.jsx
import { useState, useEffect, useCallback } from 'react';
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
  >
    {message}
  </motion.div>
);

const DailyView = () => {
  const [tasks, setTasks] = useState([]);
  const [feedback, setFeedback] = useState('');
  const [loading, setLoading] = useState(true);
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  // FIX: جایگزین alert() با toast state
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  // ── بارگذاری تودوها از بک‌اند ────────────────────────────────────────────
  const fetchTasks = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/daily/tasks`);
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

  // ── تغییر وضعیت تیک تودو ─────────────────────────────────────────────────
  const toggleTask = async (id) => {
    const task = tasks.find((t) => t.id === id);
    if (!task) return;

    const newCompleted = !task.completed;
    setTasks((prev) =>
      prev.map((t) => (t.id === id ? { ...t, completed: newCompleted } : t))
    );

    try {
      const res = await fetch(`${API_BASE}/api/daily/tasks/${id}`, {
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
    }
  };

  // ── ثبت فیدبک ────────────────────────────────────────────────────────────
  const handleSubmitFeedback = async () => {
    if (!feedback.trim()) return;
    setSubmittingFeedback(true);
    try {
      const res = await fetch(`${API_BASE}/api/daily/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feedback: feedback.trim() }),
      });
      if (!res.ok) throw new Error('خطا در ثبت فیدبک');
      // FIX: جایگزین alert() با toast
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
      <div className="p-6 h-full flex items-center justify-center">
        <div className="text-slate-400 text-sm">در حال بارگذاری...</div>
      </div>
    );
  }

  return (
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
      </AnimatePresence>
    </div>
  );
};

export default DailyView;
