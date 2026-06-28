// src/components/WeeklyView.jsx
import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Check } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

// ── Inline cell editor (جایگزین prompt()) ────────────────────────────────────
const CellEditor = ({ initialValue, onSave, onCancel }) => {
  const [value, setValue] = useState(initialValue || '');
  const inputRef = useRef(null);

  useEffect(() => {
    inputRef.current?.focus();
    inputRef.current?.select();
  }, []);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') onSave(value.trim());
    if (e.key === 'Escape') onCancel();
  };

  return (
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0.9, opacity: 0 }}
      className="absolute inset-0 z-40 bg-white rounded-lg shadow-xl border-2 border-purple-400 p-1 flex flex-col gap-1"
      onClick={(e) => e.stopPropagation()}
    >
      <input
        ref={inputRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="متن برنامه..."
        className="flex-1 text-xs px-2 py-1 rounded border border-slate-200 focus:outline-none focus:ring-1 focus:ring-purple-400 text-slate-700"
      />
      <div className="flex gap-1 justify-end">
        <button
          onClick={onCancel}
          className="p-1 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-600"
        >
          <X size={12} />
        </button>
        <button
          onClick={() => onSave(value.trim())}
          className="p-1 rounded bg-purple-500 hover:bg-purple-600 text-white"
        >
          <Check size={12} />
        </button>
      </div>
    </motion.div>
  );
};

const WeeklyView = () => {
  const [tasks, setTasks] = useState({});
  const [loading, setLoading] = useState(true);
  // FIX: جایگزین hoveredCell + prompt() با editingCell state
  const [editingCell, setEditingCell] = useState(null); // { key, day, hour }
  const [hoveredCell, setHoveredCell] = useState(null);
  const saveTimerRef = useRef(null);

  const days = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه'];
  const hours = Array.from({ length: 17 }, (_, i) => i + 7);
  const formatHour = (hour) => `${hour.toString().padStart(2, '0')}:00`;

  // ── بارگذاری از بک‌اند ─────────────────────────────────────────────────────
  const fetchSchedule = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/weekly/schedule`);
      if (!res.ok) throw new Error('خطا در دریافت برنامه هفتگی');
      const data = await res.json();
      setTasks(data.schedule || {});
    } catch (err) {
      console.error('fetchSchedule error:', err);
      setTasks({});
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSchedule();
    return () => {
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    };
  }, [fetchSchedule]);

  const scheduledSave = useCallback((newTasks) => {
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(async () => {
      try {
        await fetch(`${API_BASE}/api/weekly/schedule`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ schedule: newTasks }),
        });
      } catch (err) {
        console.error('saveSchedule error:', err);
      }
    }, 800);
  }, []);

  // FIX: کلیک باز می‌کنه editor رو (نه prompt)
  const handleCellClick = (day, hour) => {
    const key = `${day}-${hour}`;
    setEditingCell({ key, day, hour });
  };

  const handleSaveCell = (key, text) => {
    setEditingCell(null);
    if (!text) return;
    const newTasks = { ...tasks, [key]: text };
    setTasks(newTasks);
    scheduledSave(newTasks);
  };

  const handleCancelCell = () => {
    setEditingCell(null);
  };

  // FIX: راست‌کلیک حذف (همراه با تایید inline به جای window.confirm)
  const handleCellRightClick = (e, day, hour) => {
    e.preventDefault();
    const key = `${day}-${hour}`;
    if (!tasks[key]) return;
    const newTasks = { ...tasks };
    delete newTasks[key];
    setTasks(newTasks);
    scheduledSave(newTasks);
  };

  if (loading) {
    return (
      <div className="p-6 h-full flex items-center justify-center">
        <div className="text-slate-400 text-sm">در حال بارگذاری برنامه هفتگی...</div>
      </div>
    );
  }

  return (
    <div className="p-6 h-full flex flex-col">
      <div className="bg-white rounded-2xl shadow-lg p-4 flex-1 flex flex-col overflow-hidden">
        <h3 className="text-lg font-bold text-slate-700 mb-4">برنامه هفتگی</h3>

        <div className="flex-1 overflow-auto scrollbar-thin scrollbar-thumb-purple-400 scrollbar-track-slate-200">
          <table className="w-full border-collapse min-w-max">
            <thead className="sticky top-0 z-20">
              <tr>
                <th className="sticky right-0 bg-gradient-to-br from-purple-600 to-blue-600 text-white p-3 border border-slate-200 rounded-tr-xl z-30 min-w-[100px]">
                  روز / ساعت
                </th>
                {hours.map((hour) => (
                  <th
                    key={hour}
                    className="bg-gradient-to-br from-purple-500 to-blue-500 text-white p-3 border border-slate-200 min-w-[120px] text-sm font-semibold whitespace-nowrap"
                  >
                    {formatHour(hour)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {days.map((day, dayIndex) => (
                <tr key={day}>
                  <td
                    className={`sticky right-0 bg-gradient-to-l from-indigo-500 to-purple-500 text-white font-bold p-3 border border-slate-200 z-10 ${
                      dayIndex === days.length - 1 ? 'rounded-br-xl' : ''
                    }`}
                  >
                    {day}
                  </td>
                  {hours.map((hour) => {
                    const key = `${day}-${hour}`;
                    const hasTask = !!tasks[key];
                    const isEditing = editingCell?.key === key;
                    const isHovered = hoveredCell === key;

                    return (
                      <td
                        key={hour}
                        onClick={() => !isEditing && handleCellClick(day, hour)}
                        onContextMenu={(e) => handleCellRightClick(e, day, hour)}
                        onMouseEnter={() => setHoveredCell(key)}
                        onMouseLeave={() => setHoveredCell(null)}
                        className={`p-1 border border-slate-200 cursor-pointer transition-all h-[70px] relative ${
                          hasTask
                            ? 'bg-gradient-to-br from-purple-50 to-blue-50'
                            : isHovered
                            ? 'bg-slate-100'
                            : 'bg-white hover:bg-slate-50'
                        }`}
                      >
                        <AnimatePresence mode="wait">
                          {isEditing ? (
                            <CellEditor
                              key="editor"
                              initialValue={tasks[key] || ''}
                              onSave={(text) => handleSaveCell(key, text)}
                              onCancel={handleCancelCell}
                            />
                          ) : hasTask ? (
                            <motion.div
                              key="task"
                              initial={{ scale: 0.8, opacity: 0 }}
                              animate={{ scale: 1, opacity: 1 }}
                              exit={{ scale: 0.8, opacity: 0 }}
                              className="bg-gradient-to-br from-purple-500 to-blue-500 text-white text-xs p-2 rounded-lg shadow-md h-full flex items-center justify-center text-center leading-relaxed"
                            >
                              {tasks[key]}
                            </motion.div>
                          ) : null}
                        </AnimatePresence>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="text-xs text-slate-500 mt-3 text-center">
          برای افزودن/ویرایش کلیک کنید • برای حذف راست‌کلیک کنید
        </p>
      </div>
    </div>
  );
};

export default WeeklyView;
