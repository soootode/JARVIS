// src/components/WeeklyView.jsx
import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
<<<<<<< HEAD
import { apiFetch } from '../lib/apiClient';
import { X, Check, ChevronRight, ChevronLeft, CalendarDays, Sparkles } from 'lucide-react';


const DAYS = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه'];

// ISO «YYYY-MM-DD» را به‌صورت تاریخ محلی پارس می‌کند (نه UTC) تا نمایش
// روزها در منطقه‌ی زمانی کاربر یک روز جابه‌جا نشود.
const parseISODate = (iso) => {
  if (!iso) return null;
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d);
};

const faDayMonth = (date) =>
  date ? date.toLocaleDateString('fa-IR', { day: 'numeric', month: 'long' }) : '';

const faShort = (iso) => {
  const d = parseISODate(iso);
  return d ? d.toLocaleDateString('fa-IR', { day: 'numeric', month: 'long' }) : '';
};

const localTodayISO = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
};

// ── Floating cell editor modal ──────────────────────────────────────────────
// به‌صورت overlay ثابت رندر می‌شود تا هیچ‌وقت باعث اسکرول یا جابه‌جایی
// گرید پشت سر نشود.
const CellEditorModal = ({ contextLabel, initialValue, onSave, onCancel }) => {
=======
import { X, Check } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

// ── Inline cell editor (جایگزین prompt()) ────────────────────────────────────
const CellEditor = ({ initialValue, onSave, onCancel }) => {
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
  const [value, setValue] = useState(initialValue || '');
  const inputRef = useRef(null);

  useEffect(() => {
<<<<<<< HEAD
    const t = requestAnimationFrame(() => {
      inputRef.current?.focus();
      inputRef.current?.select();
    });
    return () => cancelAnimationFrame(t);
  }, []);

  const handleKeyDown = (e) => {
    e.stopPropagation();
=======
    inputRef.current?.focus();
    inputRef.current?.select();
  }, []);

  const handleKeyDown = (e) => {
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    if (e.key === 'Enter') onSave(value.trim());
    if (e.key === 'Escape') onCancel();
  };

  return (
    <motion.div
<<<<<<< HEAD
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.15 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onCancel();
      }}
    >
      <motion.div
        initial={{ scale: 0.94, y: 8, opacity: 0 }}
        animate={{ scale: 1, y: 0, opacity: 1 }}
        exit={{ scale: 0.94, y: 8, opacity: 0 }}
        transition={{ type: 'spring', stiffness: 420, damping: 30 }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-sm bg-zinc-900 border border-white/20 rounded-xl p-4 shadow-2xl shadow-black/60"
        onKeyDown={handleKeyDown}
      >
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs text-white/45">{contextLabel}</span>
          <button
            onClick={onCancel}
            className="p-1 text-white/40 hover:text-white transition-colors"
            aria-label="بستن"
          >
            <X size={14} />
          </button>
        </div>

        <input
          ref={inputRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="متن برنامه..."
          className="w-full text-sm bg-zinc-950 border border-white/15 focus:border-white/70 rounded-md outline-none text-white px-3 py-2.5 transition-colors"
        />

        <div className="flex gap-2 mt-3">
          <button
            onClick={onCancel}
            className="flex-1 py-2 text-xs rounded-md border border-zinc-700 text-white/60 hover:text-white hover:border-white/40 transition-colors"
          >
            انصراف
          </button>
          <button
            onClick={() => onSave(value.trim())}
            className="flex-1 py-2 text-xs rounded-md bg-white text-black font-medium hover:bg-white/90 transition-colors flex items-center justify-center gap-1.5"
          >
            <Check size={13} />
            ذخیره
          </button>
        </div>
      </motion.div>
=======
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
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    </motion.div>
  );
};

const WeeklyView = () => {
  const [tasks, setTasks] = useState({});
  const [loading, setLoading] = useState(true);
<<<<<<< HEAD
  const [editingCell, setEditingCell] = useState(null); // { key, dayIdx, hour }
  // ناوبری هفته: 0 = هفته جاری، 1 = بعدی، -1 = قبلی
  const [weekOffset, setWeekOffset] = useState(0);
  const [weekMeta, setWeekMeta] = useState(null); // { week_key, week_start, week_end }
  const saveTimerRef = useRef(null);

  const hours = Array.from({ length: 17 }, (_, i) => i + 7);
  const formatHour = (hour) => `${hour.toString().padStart(2, '0')}:00`;
  const todayISO = localTodayISO();

  const fetchSchedule = useCallback(async (offset) => {
    setLoading(true);
    try {
      const res = await apiFetch(`/api/weekly/schedule?week_offset=${offset}`);
      if (!res.ok) throw new Error('خطا در دریافت برنامه هفتگی');
      const data = await res.json();
      setTasks(data.schedule || {});
      setWeekMeta(data);
    } catch (err) {
      console.error('fetchSchedule error:', err);
      // داده‌ی هفته‌ی قبلی دست‌نخورده می‌ماند تا جدول فرو نریزد / خالی نشود
=======
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
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
<<<<<<< HEAD
    fetchSchedule(weekOffset);
    return () => {
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    };
  }, [fetchSchedule, weekOffset]);
=======
    fetchSchedule();
    return () => {
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    };
  }, [fetchSchedule]);
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9

  const scheduledSave = useCallback((newTasks) => {
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(async () => {
      try {
<<<<<<< HEAD
        await apiFetch(`/api/weekly/schedule?week_offset=${weekOffset}`, {
=======
        await fetch(`${API_BASE}/api/weekly/schedule`, {
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ schedule: newTasks }),
        });
      } catch (err) {
        console.error('saveSchedule error:', err);
      }
    }, 800);
<<<<<<< HEAD
  }, [weekOffset]);

  // ── کلیدهای مخزن یکپارچه: «YYYY-MM-DD|HH» با مقدار {text, completed} ─────
  const dayISOs = DAYS.map((_, i) => {
    const d = parseISODate(weekMeta?.week_start);
    if (!d) return null;
    d.setDate(d.getDate() + i);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  });
  const cellKey = (dayIdx, hour) => (dayISOs[dayIdx] ? `${dayISOs[dayIdx]}|${hour}` : `${DAYS[dayIdx]}-${hour}`);

  const handleCellClick = (key, dayIdx, hour) => {
    setEditingCell({ key, dayIdx, hour });
=======
  }, []);

  // FIX: کلیک باز می‌کنه editor رو (نه prompt)
  const handleCellClick = (day, hour) => {
    const key = `${day}-${hour}`;
    setEditingCell({ key, day, hour });
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
  };

  const handleSaveCell = (key, text) => {
    setEditingCell(null);
    if (!text) return;
<<<<<<< HEAD
    const prev = tasks[key];
    const newTasks = { ...tasks, [key]: { ...(prev || {}), text, completed: !!prev?.completed } };
=======
    const newTasks = { ...tasks, [key]: text };
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    setTasks(newTasks);
    scheduledSave(newTasks);
  };

  const handleCancelCell = () => {
    setEditingCell(null);
  };

<<<<<<< HEAD
  const handleCellRightClick = (e, key) => {
    e.preventDefault();
=======
  // FIX: راست‌کلیک حذف (همراه با تایید inline به جای window.confirm)
  const handleCellRightClick = (e, day, hour) => {
    e.preventDefault();
    const key = `${day}-${hour}`;
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    if (!tasks[key]) return;
    const newTasks = { ...tasks };
    delete newTasks[key];
    setTasks(newTasks);
    scheduledSave(newTasks);
  };

<<<<<<< HEAD
  // برچسب کانتکست مودال: «دوشنبه ۲۷ مرداد • ۱۰:00»
  const editorContext = editingCell
    ? `${DAYS[editingCell.dayIdx]} ${faDayMonth(parseISODate(dayISOs[editingCell.dayIdx]))} • ${formatHour(editingCell.hour)}`
    : '';

  const isEmpty = !loading && Object.keys(tasks).length === 0;

  const offsetLabel =
    weekOffset === 0
      ? 'این هفته'
      : weekOffset > 0
        ? `${weekOffset.toLocaleString('fa-IR')} هفته بعد`
        : `${Math.abs(weekOffset).toLocaleString('fa-IR')} هفته قبل`;

  return (
    <div className="p-3 sm:p-6 h-full flex flex-col bg-zinc-950">
      <div className="border border-zinc-800 rounded-xl p-3 sm:p-4 flex-1 flex flex-col overflow-hidden">
        {/* ── نوار بالا: عنوان + ناوبری هفته ──────────────────────────────── */}
        <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
          <h3 className="text-sm text-white/80">برنامه هفتگی</h3>

          <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
            {/* بازه‌ی صریح شنبه تا جمعه — مرزهای هفته همیشه مشخص */}
            {weekMeta?.week_start && weekMeta?.week_end && (
              <span className="text-xs text-white/50 whitespace-nowrap" dir="rtl">
                <span className="text-white/30">شنبه</span> {faShort(weekMeta.week_start)}
                <span className="text-white/25 mx-1.5">تا</span>
                <span className="text-white/30">جمعه</span> {faShort(weekMeta.week_end)}
              </span>
            )}

            {weekOffset !== 0 && (
              <button
                onClick={() => setWeekOffset(0)}
                className="text-xs px-2.5 py-1 rounded-full border border-zinc-700 text-white/60 hover:text-white hover:border-white/50 transition-colors"
              >
                امروز
              </button>
            )}

            <div className="flex items-center border border-zinc-800 rounded-lg overflow-hidden divide-x divide-x-reverse divide-zinc-800">
              <button
                onClick={() => setWeekOffset((o) => o - 1)}
                className="p-2 text-white/60 hover:text-white hover:bg-white/5 active:bg-white/10 transition-colors"
                aria-label="هفته قبل"
              >
                <ChevronRight size={16} />
              </button>
              <span className="px-3 text-xs text-white/70 min-w-[92px] text-center tabular-nums">
                {offsetLabel}
              </span>
              <button
                onClick={() => setWeekOffset((o) => o + 1)}
                className="p-2 text-white/60 hover:text-white hover:bg-white/5 active:bg-white/10 transition-colors"
                aria-label="هفته بعد"
              >
                <ChevronLeft size={16} />
              </button>
            </div>
          </div>
        </div>

        {/* ── محتوای تقویم: در حین fetch داده‌ی قبلی حفظ و فقط کم‌رنگ می‌شود ── */}
        <div
          className={`relative flex-1 overflow-auto scrollbar-thin transition-opacity duration-200 ${
            loading ? 'opacity-40 pointer-events-none select-none' : 'opacity-100'
          }`}
        >
          {/* ── Empty state هفته‌ی خالی ─────────────────────────────────────── */}
          {isEmpty && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
              className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-4 text-center pointer-events-none px-6"
            >
              <div className="w-16 h-16 rounded-2xl border border-dashed border-zinc-700 flex items-center justify-center">
                <CalendarDays size={26} className="text-white/25" />
              </div>
              <div className="text-white/45 text-sm leading-relaxed max-w-xs">
                این هفته هنوز خالی است.
                <br />
                <span className="text-xs text-white/30">
                  روی هر خانه کلیک کنید تا برنامه دستی اضافه کنید، یا از جارویس بخواهید برایتان بچیند.
                </span>
              </div>
              <div className="flex items-center gap-1.5 text-[11px] text-indigo-300/60">
                <Sparkles size={12} />
                پیشنهاد: «سه‌شنبه ساعت ۱۰ برای مطالعه ریاضی وقت بذار»
              </div>
            </motion.div>
          )}

          {/* table-fixed + colgroup: عرض ستون‌ها قفل می‌شود و هرگز با محتوای
              بلند کش نمی‌آید؛ ارتفاع ردیف‌ها هم h-16 ثابت است. */}
          <table className="w-full table-fixed border-collapse">
            <colgroup>
              <col className="w-[86px] sm:w-[120px]" />
              {hours.map((hour) => (
                <col key={hour} className="min-w-[64px]" />
              ))}
            </colgroup>
            <thead className="sticky top-0 z-20">
              <tr>
                <th className="sticky right-0 bg-zinc-950 text-white/60 p-2 sm:p-3 border border-zinc-800 z-30 font-normal text-[11px] sm:text-xs text-right whitespace-nowrap">
=======
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
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
                  روز / ساعت
                </th>
                {hours.map((hour) => (
                  <th
                    key={hour}
<<<<<<< HEAD
                    className="bg-zinc-950 text-white/55 p-2 sm:p-3 border border-zinc-800 text-[11px] sm:text-xs font-normal whitespace-nowrap tabular-nums overflow-hidden text-ellipsis"
=======
                    className="bg-gradient-to-br from-purple-500 to-blue-500 text-white p-3 border border-slate-200 min-w-[120px] text-sm font-semibold whitespace-nowrap"
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
                  >
                    {formatHour(hour)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
<<<<<<< HEAD
              {DAYS.map((day, dayIdx) => {
                const cellISO = dayISOs[dayIdx];
                const isTodayRow = cellISO === todayISO;

                return (
                  <tr key={`row-${cellISO || dayIdx}`}>
                    <td
                      className={`sticky right-0 p-2 sm:p-3 border border-zinc-800 z-10 align-middle overflow-hidden ${
                        isTodayRow ? 'bg-zinc-900' : 'bg-zinc-950'
                      }`}
                    >
                      <div className={`text-xs sm:text-sm truncate ${isTodayRow ? 'text-white font-semibold' : 'text-white/85'}`}>
                        {day}
                        {isTodayRow && (
                          <span className="mr-1.5 inline-block w-1.5 h-1.5 rounded-full bg-indigo-400 align-middle" />
                        )}
                      </div>
                      {/* برچسب تاریخ زنده: «۲۷ مرداد» */}
                      {cellISO && (
                        <div className={`text-[10px] sm:text-xs mt-0.5 truncate ${isTodayRow ? 'text-indigo-300' : 'text-white/35'}`}>
                          {faDayMonth(parseISODate(cellISO))}
                        </div>
                      )}
                    </td>
                    {hours.map((hour) => {
                      const key = cellKey(dayIdx, hour);
                      const item = tasks[key];
                      const hasTask = !!item;
                      const isCompleted = !!item?.completed;

                      return (
                        <td
                          key={`cell-${cellISO || dayIdx}-${hour}`}
                          onClick={() => handleCellClick(key, dayIdx, hour)}
                          onContextMenu={(e) => handleCellRightClick(e, key)}
                          title={hasTask ? item.text : undefined}
                          className={`group p-1 border border-zinc-800 cursor-pointer transition-colors h-16 relative align-top overflow-hidden ${
                            isTodayRow && !hasTask ? 'bg-indigo-500/[0.04]' : ''
                          } ${!hasTask ? 'hover:bg-white/[0.05]' : ''}`}
                        >
                          {hasTask ? (
                            <motion.div
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              transition={{ duration: 0.18 }}
                              className={`h-full w-full rounded-md text-[11px] sm:text-xs p-2 flex items-center justify-start text-right leading-snug overflow-hidden text-ellipsis ${
                                isCompleted
                                  ? 'bg-emerald-400/[0.08] border border-emerald-400/40 border-r-2 border-r-emerald-400'
                                  : 'bg-white/[0.08] border border-white/25 border-r-2 border-r-indigo-400'
                              }`}
                              style={{ direction: 'rtl' }}
                            >
                              <span
                                className={`line-clamp-2 break-words min-w-0 ${
                                  isCompleted ? 'line-through text-emerald-100/80' : 'text-white/95'
                                }`}
                              >
                                {item.text}
                              </span>
                            </motion.div>
                          ) : (
                            <div className="hidden group-hover:flex items-center justify-center h-full w-full text-white/20 pointer-events-none">
                              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                                <path d="M6 1v10M1 6h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                              </svg>
                            </div>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
=======
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
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
            </tbody>
          </table>
        </div>

<<<<<<< HEAD
        <p className="hidden sm:block text-[11px] text-white/30 mt-3 text-center">
          برای افزودن/ویرایش کلیک کنید • برای حذف راست‌کلیک کنید
        </p>
      </div>

      {/* ── مودال شناور ویرایش سلول ─────────────────────────────────────── */}
      <AnimatePresence>
        {editingCell && (
          <CellEditorModal
            key={editingCell.key}
            contextLabel={editorContext}
            initialValue={tasks[editingCell.key]?.text || ''}
            onSave={(text) => handleSaveCell(editingCell.key, text)}
            onCancel={handleCancelCell}
          />
        )}
      </AnimatePresence>
=======
        <p className="text-xs text-slate-500 mt-3 text-center">
          برای افزودن/ویرایش کلیک کنید • برای حذف راست‌کلیک کنید
        </p>
      </div>
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    </div>
  );
};

export default WeeklyView;
