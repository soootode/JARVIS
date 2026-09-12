// src/components/NotificationPoller.jsx
// ─────────────────────────────────────────────────────
// در App.jsx یا root layout اضافه کن: <NotificationPoller />
// ─────────────────────────────────────────────────────

import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { apiFetch } from '../lib/apiClient';
import { Bell, X } from 'lucide-react';

const POLL_INTERVAL_MS = 30_000; // هر 30 ثانیه

const NotificationToast = ({ notif, onDismiss }) => (
  <motion.div
    initial={{ x: 80, opacity: 0 }}
    animate={{ x: 0, opacity: 1 }}
    exit={{ x: 80, opacity: 0 }}
    transition={{ type: 'spring', stiffness: 300, damping: 25 }}
    className="flex items-start gap-3 bg-[#0a0a0b] border border-white/25 p-4 max-w-xs w-full"
  >
    <div className="mt-0.5 text-white flex-shrink-0">
      <Bell size={16} />
    </div>
    <div className="flex-1 min-w-0">
      <p className="text-sm text-white leading-snug">{notif.title}</p>
      {notif.message && (
        <p className="text-xs text-white/45 mt-1 leading-relaxed">{notif.message}</p>
      )}
    </div>
    <button
      onClick={() => onDismiss(notif.id)}
      className="flex-shrink-0 text-white/30 hover:text-white transition-colors"
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
      const res = await apiFetch(`/api/notifications/pending`);
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
      await apiFetch(`/api/notifications/${id}/dismiss`, { method: 'POST' });
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
