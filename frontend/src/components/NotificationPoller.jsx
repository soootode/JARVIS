// src/components/NotificationPoller.jsx
// ─────────────────────────────────────────────────────
// در App.jsx یا root layout اضافه کن: <NotificationPoller />
// ─────────────────────────────────────────────────────

import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, X } from 'lucide-react';

const API_BASE = 'http://localhost:8000';
const POLL_INTERVAL_MS = 30_000; // هر 30 ثانیه

const NotificationToast = ({ notif, onDismiss }) => (
  <motion.div
    initial={{ x: 80, opacity: 0 }}
    animate={{ x: 0, opacity: 1 }}
    exit={{ x: 80, opacity: 0 }}
    transition={{ type: 'spring', stiffness: 300, damping: 25 }}
    className="flex items-start gap-3 bg-white border border-purple-200 shadow-xl rounded-2xl p-4 max-w-xs w-full"
  >
    <div className="mt-0.5 p-2 rounded-xl bg-purple-100 text-purple-600 flex-shrink-0">
      <Bell size={16} />
    </div>
    <div className="flex-1 min-w-0">
      <p className="text-sm font-semibold text-slate-700 leading-snug">{notif.title}</p>
      {notif.message && (
        <p className="text-xs text-slate-500 mt-1 leading-relaxed">{notif.message}</p>
      )}
    </div>
    <button
      onClick={() => onDismiss(notif.id)}
      className="flex-shrink-0 text-slate-300 hover:text-slate-500 transition-colors"
    >
      <X size={16} />
    </button>
  </motion.div>
);

const NotificationPoller = () => {
  const [queue, setQueue] = useState([]);
  // Set برای جلوگیری از نمایش تکراری همان نوتیف
  const seenRef = useRef(new Set());

  const pollNotifications = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/notifications/pending`);
      if (!res.ok) return;
      const data = await res.json();
      const fresh = (data.notifications || []).filter(
        (n) => !seenRef.current.has(n.id)
      );
      if (fresh.length > 0) {
        fresh.forEach((n) => seenRef.current.add(n.id));
        setQueue((prev) => [...prev, ...fresh]);
      }
    } catch {
      // silent fail — بک‌اند ممکنه موقتاً down باشه
    }
  };

  useEffect(() => {
    pollNotifications(); // بلافاصله یک بار چک کن
    const interval = setInterval(pollNotifications, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, []);

  const dismiss = async (id) => {
    setQueue((prev) => prev.filter((n) => n.id !== id));
    try {
      await fetch(`${API_BASE}/api/notifications/${id}/dismiss`, { method: 'POST' });
    } catch {
      // silent
    }
  };

  // auto-dismiss اولین نوتیف بعد از 8 ثانیه
  useEffect(() => {
    if (queue.length === 0) return;
    const timer = setTimeout(() => dismiss(queue[0].id), 8000);
    return () => clearTimeout(timer);
  }, [queue]);

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 items-end pointer-events-none">
      <AnimatePresence>
        {queue.slice(0, 3).map((notif) => (
          <div key={notif.id} className="pointer-events-auto">
            <NotificationToast notif={notif} onDismiss={dismiss} />
          </div>
        ))}
      </AnimatePresence>
    </div>
  );
};

export default NotificationPoller;
