// src/components/ChatView.jsx
import { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const ChatView = () => {
  const [messages, setMessages] = useState([
    { id: 1, sender: 'jarvis', text: 'سلام! من جارویس هستم. چطور می‌تونم کمکتون کنم؟', timestamp: new Date() }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || loading) return;

    const userInput = inputValue.trim();
    const newMessage = {
      id: Date.now(),
      sender: 'user',
      text: userInput,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newMessage]);
    setInputValue('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userInput })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      // FIX: removed dead-code branch that was patching an old backend bug
      const aiText = data.response || 'پاسخی دریافت نشد';

      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'jarvis',
        text: aiText,
        timestamp: new Date()
      }]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'jarvis',
        text: 'متأسفم، خطایی رخ داد. لطفاً دوباره تلاش کنید.',
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-hide">
        {messages.map((msg) => (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[75%] px-5 py-3 rounded-2xl shadow-md ${
                msg.sender === 'user'
                  ? 'bg-gradient-to-br from-purple-500 to-blue-500 text-white'
                  : 'bg-white text-slate-700'
              }`}
            >
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>
              <p className={`text-xs mt-1 ${msg.sender === 'user' ? 'text-purple-100' : 'text-slate-400'}`}>
                {msg.timestamp.toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </motion.div>
        ))}

        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start"
          >
            <div className="bg-white text-slate-700 px-5 py-3 rounded-2xl shadow-md">
              <div className="flex gap-2">
                {[0, 150, 300].map((delay) => (
                  <div
                    key={delay}
                    className="w-2 h-2 bg-purple-500 rounded-full animate-bounce"
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
      <div className="p-4 bg-white/50 backdrop-blur-sm border-t border-slate-200">
        <div className="flex gap-3">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
            placeholder="پیام خود را بنویسید..."
            disabled={loading}
            className="flex-1 px-4 py-3 rounded-xl bg-white text-slate-700 placeholder-slate-400 border border-slate-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all disabled:opacity-50"
          />
          <button
            onClick={handleSendMessage}
            disabled={loading || !inputValue.trim()}
            className="px-5 py-3 bg-gradient-to-br from-purple-500 to-blue-500 text-white rounded-xl font-semibold hover:shadow-lg transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send size={20} />
            <span>ارسال</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatView;
