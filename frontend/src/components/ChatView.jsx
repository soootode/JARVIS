// src/components/ChatView.jsx
import { useState, useRef, useEffect } from 'react';
import { Send, CalendarCheck, AlertTriangle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { apiFetch } from '../lib/apiClient';

const WELCOME_MESSAGE = { id: 'welcome', sender: 'jarvis', text: 'سلام! من جارویس هستم. چطور می‌تونم کمکتون کنم؟', timestamp: new Date() };

const NOTE_SEPARATOR = '\n---\n';
const NOTE_TITLE_RE = /^[^\n]*📅[^\n]*\n?/;

// پیام جارویس می‌تونه یک «یادداشت سیستم» (نتیجه‌ی ثبت خودکار در تقویم)
// انتهای متن داشته باشه؛ اون رو جدا می‌کنیم تا به‌شکل کارت متمایز رندر بشه.
const parseMessageParts = (text) => {
  const idx = text ? text.indexOf(NOTE_SEPARATOR) : -1;
  if (idx === -1) return { body: text, note: null };
  let note = text.slice(idx + NOTE_SEPARATOR.length).replace(NOTE_TITLE_RE, '').trim();
  const items = note
    ? note.split('\n').map((l) => l.replace(/^[•\-–]\s*/, '').trim()).filter(Boolean)
    : [];
  return { body: text.slice(0, idx).trim(), note: items.length > 0 ? items : null };
};

const PlannerNoteCard = ({ items }) => (
  <motion.div
    initial={{ opacity: 0, y: 8 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: 0.1 }}
    className="mt-3 rounded-lg border border-indigo-400/30 bg-indigo-500/[0.07] p-3"
    dir="rtl"
  >
    <div className="flex items-center gap-1.5 mb-2">
      <CalendarCheck size={13} className="text-indigo-300" />
      <span className="text-[11px] font-medium text-indigo-200">ثبت شد در برنامه‌ات</span>
    </div>
    <ul className="space-y-1.5">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2 text-xs leading-relaxed text-white/80">
          <span className="mt-[7px] w-1 h-1 rounded-full bg-indigo-300/70 flex-shrink-0" />
          {item}
        </li>
      ))}
    </ul>
  </motion.div>
);

const ChatView = () => {
  const [messages, setMessages] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    (async () => {
      try {
        const res = await apiFetch('/api/conversation-history?limit=100');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const history = (data.history || []).map((m) => ({
          id: m.id,
          sender: m.role === 'user' ? 'user' : 'jarvis',
          text: m.content,
          timestamp: m.created_at ? new Date(m.created_at) : new Date(),
        }));
        setMessages(history.length > 0 ? history : [WELCOME_MESSAGE]);
      } catch (err) {
        console.error('fetch history error:', err);
        setMessages([WELCOME_MESSAGE]);
      } finally {
        setHistoryLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || loading) return;

    const userInput = inputValue.trim();
    setMessages(prev => [...prev, { id: Date.now(), sender: 'user', text: userInput, timestamp: new Date() }]);
    setInputValue('');
    setLoading(true);

    try {
      const response = await apiFetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userInput })
      });

      if (!response.ok) {
        let detail = null;
        try {
          const errBody = await response.json();
          detail = errBody.detail;
        } catch { /* ignore */ }
        throw new Error(detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'jarvis',
        text: data.response || 'پاسخی دریافت نشد',
        timestamp: new Date()
      }]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'jarvis',
        text: error.message && !error.message.startsWith('HTTP') ? error.message : 'متأسفم، خطایی رخ داد. لطفاً دوباره تلاش کنید.',
        isError: true,
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  if (historyLoading) {
    return (
      <div className="flex flex-col h-full bg-zinc-950 items-center justify-center">
        <div className="text-white/40 text-sm">در حال بارگذاری مکالمه...</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-zinc-950">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 scrollbar-hide">
        <AnimatePresence initial={false}>
          {messages.map((msg) => {
            const { body, note } = msg.sender === 'jarvis' ? parseMessageParts(msg.text) : { body: msg.text, note: null };
            return (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ type: 'spring', stiffness: 400, damping: 32 }}
                className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] sm:max-w-[75%] px-4 sm:px-5 py-3 rounded-xl ${
                    msg.sender === 'user'
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-950/50'
                      : msg.isError
                        ? 'bg-red-500/[0.08] border border-red-400/40 text-red-100'
                        : 'bg-zinc-900 border border-zinc-700/70 text-white/90'
                  }`}
                >
                  {msg.isError ? (
                    <>
                      <div className="flex items-center gap-1.5 mb-1.5">
                        <AlertTriangle size={13} className="text-red-300" />
                        <span className="text-[11px] font-medium text-red-200">خطا</span>
                      </div>
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                    </>
                  ) : (
                    <>
                      <p className={`text-sm leading-relaxed whitespace-pre-wrap ${body ? '' : 'hidden'}`}>{body}</p>
                      {note && <PlannerNoteCard items={note} />}
                    </>
                  )}
                  <p className={`text-[11px] mt-1.5 tabular-nums ${
                    msg.sender === 'user'
                      ? 'text-indigo-200/60'
                      : msg.isError
                        ? 'text-red-200/40'
                        : 'text-white/30'
                  }`}>
                    {msg.timestamp.toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>

        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start"
          >
            <div className="bg-zinc-900 border border-zinc-700/70 rounded-xl px-5 py-3.5">
              <div className="flex gap-2">
                {[0, 150, 300].map((delay) => (
                  <div
                    key={delay}
                    className="w-1.5 h-1.5 bg-white/60 rounded-full animate-bounce"
                    style={{ animationDelay: `${delay}ms` }}
                  />
                ))}
              </div>
            </div>
          </motion.div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-3 sm:p-4 border-t border-zinc-800">
        <div className="flex gap-3">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
            placeholder="پیام خود را بنویسید..."
            disabled={loading}
            maxLength={4000}
            className="flex-1 min-w-0 bg-transparent border-0 border-b border-white/25 focus:border-white/70 outline-none text-sm sm:text-base text-white placeholder-white/30 py-2 px-1 transition-colors disabled:opacity-50"
          />
          <button
            onClick={handleSendMessage}
            disabled={loading || !inputValue.trim()}
            className="relative px-5 sm:px-6 py-2.5 group disabled:opacity-40 disabled:cursor-not-allowed active:scale-[0.98] transition-transform flex-shrink-0"
          >
            <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 44" preserveAspectRatio="none" style={{ overflow: 'visible' }}>
              <path
                d="M 3 5 C 25 3, 70 6, 97 4 C 99 15, 98 28, 97 39 C 70 41, 25 40, 3 41 C 1 28, 2 15, 3 5 Z"
                fill="none" stroke="#ffffff" strokeWidth="1.4"
                className="transition-all duration-200 group-hover:stroke-[1.8]"
              />
            </svg>
            <span className="relative z-10 flex items-center gap-2 text-sm text-white">
              {loading ? (
                <svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeOpacity="0.25" />
                  <path d="M22 12a10 10 0 0 1-10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
                </svg>
              ) : (
                <Send size={16} />
              )}
              ارسال
            </span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatView;
