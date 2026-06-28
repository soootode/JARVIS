"""
memory_manager.py - Jarvis-You (نسخه ۲)
مدیریت حافظه با SQLAlchemy - سازگار با SQLite و PostgreSQL
"""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func

from database import (
    ContextSnapshot,
    Conversation,
    DailyState,
    EventTask,
    Goal,
    Habit,
    HabitLog,
    Persona,
    Psychology,
    get_session,
    init_db,
)

MAX_HISTORY_FOR_LLM = 20


# ── JSON helper (SQLite/PostgreSQL سازگار) ─────────────────────────────────────

def _loads(val: Any) -> Any:
    """رشته JSON را در SQLite به شیء تبدیل می‌کند؛ در PostgreSQL مقدار همیشه شیء است."""
    if val is None:
        return None
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return val
    return val  # PostgreSQL JSONB از قبل parse شده است


def _dumps(val: Any) -> Any:
    """در SQLite شیء را به رشته JSON تبدیل می‌کند؛ در PostgreSQL همان شیء را برمی‌گرداند."""
    from database import _IS_POSTGRES
    if val is None:
        return None
    if _IS_POSTGRES:
        return val  # SQLAlchemy JSONB خودش هندل می‌کند
    return json.dumps(val, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════════════════════
# MemoryManager
# ══════════════════════════════════════════════════════════════════════════════

class MemoryManager:
    """
    رابط اصلی برای همه عملیات حافظه Jarvis-You.
    هر instance یک session_id دارد که تاریخچه مکالمه جاری را نگه می‌دارد.
    """

    def __init__(self, session_id: Optional[str] = None) -> None:
        init_db()
        self.session_id: str = session_id or str(uuid.uuid4())
        self._ensure_singleton_rows()

    # ── Bootstrap ──────────────────────────────────────────────────────────────

    def _ensure_singleton_rows(self) -> None:
        """Persona و Psychology باید همیشه یک ردیف با id=1 داشته باشند."""
        with get_session() as session:
            if not session.get(Persona, 1):
                session.add(Persona(id=1))
            if not session.get(Psychology, 1):
                session.add(Psychology(id=1))
            session.commit()

    # ══════════════════════════════════════════════════════════════════════════
    # لایه ۱ - Static Memory
    # ══════════════════════════════════════════════════════════════════════════

    # ── Persona ────────────────────────────────────────────────────────────────

    def get_persona(self) -> Dict[str, Any]:
        with get_session() as session:
            p = session.get(Persona, 1)
            if not p:
                return {}
            return {
                "preferred_name": p.preferred_name,
                "age": p.age,
                "gender": p.gender,
                "location": p.location,
                "occupation": p.occupation,
                "education_level": p.education_level,
                "languages": _loads(p.languages),
                "core_values": _loads(p.core_values),
                "life_philosophy": p.life_philosophy,
                "mbti": p.mbti,
                "enneagram": p.enneagram,
            }

    def update_persona(self, **kwargs: Any) -> None:
        """
        به‌روزرسانی فیلدهای Persona.
        مثال: update_persona(preferred_name="علی", age=22, mbti="INTJ")
        """
        _json_fields = {"languages", "core_values"}
        with get_session() as session:
            p = session.get(Persona, 1)
            if not p:
                p = Persona(id=1)
                session.add(p)
            for key, val in kwargs.items():
                if hasattr(p, key):
                    setattr(p, key, _dumps(val) if key in _json_fields else val)
            session.commit()

    # ── Psychology ─────────────────────────────────────────────────────────────

    def get_psychology(self) -> Dict[str, Any]:
        with get_session() as session:
            ps = session.get(Psychology, 1)
            if not ps:
                return {}
            return {
                "stress_triggers": _loads(ps.stress_triggers) or [],
                "motivators": _loads(ps.motivators) or [],
                "fear_patterns": _loads(ps.fear_patterns) or [],
                "cognitive_biases": _loads(ps.cognitive_biases) or [],
                "coping_strategies": _loads(ps.coping_strategies) or [],
                "attachment_style": ps.attachment_style,
                "communication_style": ps.communication_style,
                "decision_making_style": ps.decision_making_style,
                "procrastination_patterns": _loads(ps.procrastination_patterns) or [],
            }

    def append_to_psychology_list(self, field: str, item: str) -> None:
        """
        یک آیتم جدید به لیست‌های Psychology اضافه می‌کند (بدون تکرار).
        مثال: append_to_psychology_list("stress_triggers", "مهلت فوری")
        """
        _list_fields = {
            "stress_triggers", "motivators", "fear_patterns",
            "cognitive_biases", "coping_strategies", "procrastination_patterns",
        }
        if field not in _list_fields:
            return
        with get_session() as session:
            ps = session.get(Psychology, 1)
            if not ps:
                return
            current: list = _loads(getattr(ps, field)) or []
            if item not in current:
                current.append(item)
                setattr(ps, field, _dumps(current))
                session.commit()

    def update_psychology(self, **kwargs: Any) -> None:
        _json_fields = {
            "stress_triggers", "motivators", "fear_patterns",
            "cognitive_biases", "coping_strategies", "procrastination_patterns",
        }
        with get_session() as session:
            ps = session.get(Psychology, 1)
            if not ps:
                return
            for key, val in kwargs.items():
                if hasattr(ps, key):
                    setattr(ps, key, _dumps(val) if key in _json_fields else val)
            session.commit()

    # ── Goals ──────────────────────────────────────────────────────────────────

    def add_goal(
        self,
        title: str,
        description: str = "",
        category: str = "",
        priority: int = 5,
        timeframe: str = "mid",
        target_date: Optional[datetime] = None,
        milestones: Optional[list] = None,
    ) -> int:
        """هدف جدید اضافه می‌کند و id را برمی‌گرداند."""
        with get_session() as session:
            g = Goal(
                title=title,
                description=description,
                category=category,
                priority=priority,
                timeframe=timeframe,
                target_date=target_date,
                milestones=_dumps(milestones or []),
                status="active",
            )
            session.add(g)
            session.commit()
            session.refresh(g)
            return g.id

    def get_active_goals(self) -> List[Dict[str, Any]]:
        with get_session() as session:
            goals = (
                session.query(Goal)
                .filter(Goal.status == "active")
                .order_by(Goal.priority)
                .all()
            )
            return [
                {
                    "id": g.id,
                    "title": g.title,
                    "category": g.category,
                    "priority": g.priority,
                    "timeframe": g.timeframe,
                    "progress_percent": g.progress_percent,
                    "milestones": _loads(g.milestones) or [],
                }
                for g in goals
            ]

    def update_goal_progress(self, goal_id: int, progress_percent: float) -> None:
        with get_session() as session:
            g = session.get(Goal, goal_id)
            if g:
                g.progress_percent = progress_percent
                if progress_percent >= 100:
                    g.status = "completed"
                session.commit()

    # ══════════════════════════════════════════════════════════════════════════
    # لایه ۲ - Episodic Memory
    # ══════════════════════════════════════════════════════════════════════════

    # ── Daily State ────────────────────────────────────────────────────────────

    def update_daily_state(
        self,
        mood: Optional[str] = None,
        energy: Optional[str] = None,
        stress_level: Optional[str] = None,
        focus_level: Optional[str] = None,
        sleep_hours: Optional[float] = None,
        sleep_quality: Optional[str] = None,
        current_tasks: Optional[List[str]] = None,
        blockers: Optional[List[str]] = None,
        notes: Optional[str] = None,
    ) -> None:
        """وضعیت امروز را ایجاد یا به‌روز می‌کند."""
        today = date.today().isoformat()
        with get_session() as session:
            ds = session.query(DailyState).filter_by(date=today).first()
            if not ds:
                ds = DailyState(date=today)
                session.add(ds)
            if mood is not None: ds.mood = mood
            if energy is not None: ds.energy = energy
            if stress_level is not None: ds.stress_level = stress_level
            if focus_level is not None: ds.focus_level = focus_level
            if sleep_hours is not None: ds.sleep_hours = sleep_hours
            if sleep_quality is not None: ds.sleep_quality = sleep_quality
            if current_tasks is not None: ds.current_tasks = _dumps(current_tasks)
            if blockers is not None: ds.blockers = _dumps(blockers)
            if notes is not None: ds.notes = notes
            ds.updated_at = datetime.utcnow()
            session.commit()

    def get_today_state(self) -> Dict[str, Any]:
        today = date.today().isoformat()
        with get_session() as session:
            ds = session.query(DailyState).filter_by(date=today).first()
            if not ds:
                return {}
            return {
                "date": ds.date,
                "mood": ds.mood,
                "energy": ds.energy,
                "stress_level": ds.stress_level,
                "focus_level": ds.focus_level,
                "sleep_hours": ds.sleep_hours,
                "current_tasks": _loads(ds.current_tasks) or [],
                "blockers": _loads(ds.blockers) or [],
                "notes": ds.notes,
            }

    def get_recent_daily_states(self, days: int = 7) -> List[Dict[str, Any]]:
        with get_session() as session:
            rows = (
                session.query(DailyState)
                .order_by(desc(DailyState.date))
                .limit(days)
                .all()
            )
            return [
                {
                    "date": r.date, "mood": r.mood, "energy": r.energy,
                    "stress_level": r.stress_level,
                    "current_tasks": _loads(r.current_tasks) or [],
                }
                for r in reversed(rows)
            ]

    # ── Events & Tasks ─────────────────────────────────────────────────────────

    def add_event(
        self,
        event_type: str,
        title: str,
        description: str = "",
        impact_level: int = 5,
        emotion: Optional[str] = None,
        lesson_learned: Optional[str] = None,
        related_goal_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> int:
        with get_session() as session:
            e = EventTask(
                event_type=event_type,
                title=title,
                description=description,
                impact_level=impact_level,
                emotion=emotion,
                lesson_learned=lesson_learned,
                related_goal_id=related_goal_id,
                tags=_dumps(tags or []),
            )
            session.add(e)
            session.commit()
            session.refresh(e)
            return e.id

    def get_recent_events(self, limit: int = 10, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_session() as session:
            q = session.query(EventTask).order_by(desc(EventTask.occurred_at))
            if event_type:
                q = q.filter(EventTask.event_type == event_type)
            rows = q.limit(limit).all()
            return [
                {
                    "id": r.id,
                    "event_type": r.event_type,
                    "title": r.title,
                    "description": r.description,
                    "impact_level": r.impact_level,
                    "emotion": r.emotion,
                    "lesson_learned": r.lesson_learned,
                    "tags": _loads(r.tags) or [],
                    "occurred_at": r.occurred_at.isoformat() if r.occurred_at else None,
                }
                for r in rows
            ]

    # ── Habits ─────────────────────────────────────────────────────────────────

    def add_habit(
        self,
        name: str,
        habit_type: str = "positive",
        frequency: str = "daily",
        target_count: int = 1,
        category: str = "",
        description: str = "",
    ) -> int:
        with get_session() as session:
            h = Habit(
                name=name,
                description=description,
                habit_type=habit_type,
                frequency=frequency,
                target_count=target_count,
                category=category,
            )
            session.add(h)
            session.commit()
            session.refresh(h)
            return h.id

    def log_habit(
        self,
        habit_id: int,
        completed: bool = True,
        count: int = 1,
        quality: Optional[int] = None,
        notes: str = "",
    ) -> None:
        today = date.today().isoformat()
        with get_session() as session:
            log = HabitLog(
                habit_id=habit_id,
                date=today,
                completed=completed,
                count=count,
                quality=quality,
                notes=notes,
            )
            session.add(log)
            # به‌روزرسانی streak
            habit = session.get(Habit, habit_id)
            if habit:
                if completed:
                    habit.streak_current += 1
                    habit.streak_best = max(habit.streak_best, habit.streak_current)
                else:
                    habit.streak_current = 0
                habit.updated_at = datetime.utcnow()
            session.commit()

    def get_active_habits(self) -> List[Dict[str, Any]]:
        with get_session() as session:
            habits = session.query(Habit).filter_by(is_active=True).all()
            return [
                {
                    "id": h.id,
                    "name": h.name,
                    "habit_type": h.habit_type,
                    "frequency": h.frequency,
                    "category": h.category,
                    "streak_current": h.streak_current,
                    "streak_best": h.streak_best,
                }
                for h in habits
            ]

    # ══════════════════════════════════════════════════════════════════════════
    # لایه ۳ - Working Memory
    # ══════════════════════════════════════════════════════════════════════════

    # ── Conversations ──────────────────────────────────────────────────────────

    def add_conversation(
        self,
        user_message: str,
        assistant_message: str,
        model_used: str = "gemini-2.0-flash",
    ) -> None:
        with get_session() as session:
            session.add_all([
                Conversation(
                    session_id=self.session_id,
                    role="user",
                    content=user_message,
                    model_used=model_used,
                ),
                Conversation(
                    session_id=self.session_id,
                    role="assistant",
                    content=assistant_message,
                    model_used=model_used,
                ),
            ])
            session.commit()

    def get_conversation_history(self, limit: int = MAX_HISTORY_FOR_LLM) -> List[Dict[str, str]]:
        """آخرین N پیام را برای ارسال به LLM برمی‌گرداند."""
        with get_session() as session:
            rows = (
                session.query(Conversation)
                .order_by(desc(Conversation.id))
                .limit(limit)
                .all()
            )
            return [{"role": r.role, "content": r.content} for r in reversed(rows)]

    def get_all_conversations(self) -> List[Dict[str, Any]]:
        with get_session() as session:
            rows = session.query(Conversation).order_by(Conversation.id).all()
            return [
                {
                    "id": r.id,
                    "session_id": r.session_id,
                    "role": r.role,
                    "content": r.content,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]

    # ── Context Snapshots ──────────────────────────────────────────────────────

    def save_context_snapshot(
        self,
        summary: str,
        active_tasks: Optional[List[str]] = None,
        key_decisions: Optional[List[str]] = None,
        open_questions: Optional[List[str]] = None,
        mood_at_end: Optional[str] = None,
        topics_discussed: Optional[List[str]] = None,
    ) -> None:
        """
        در پایان هر سشن فراخوانی می‌شود.
        خلاصه مکالمه و تسک‌های باز را در دیتابیس ذخیره می‌کند.
        """
        with get_session() as session:
            count = (
                session.query(func.count(Conversation.id))
                .filter_by(session_id=self.session_id)
                .scalar()
                or 0
            )
            snap = ContextSnapshot(
                session_id=self.session_id,
                summary=summary,
                active_tasks=_dumps(active_tasks or []),
                key_decisions=_dumps(key_decisions or []),
                open_questions=_dumps(open_questions or []),
                mood_at_end=mood_at_end,
                topics_discussed=_dumps(topics_discussed or []),
                message_count=count,
            )
            session.add(snap)
            session.commit()

    def get_last_snapshot(self) -> Optional[Dict[str, Any]]:
        """
        آخرین snapshot سشن قبلی را برمی‌گرداند.
        در ابتدای چت جدید برای context-loading استفاده می‌شود.
        """
        with get_session() as session:
            snap = (
                session.query(ContextSnapshot)
                .filter(ContextSnapshot.session_id != self.session_id)
                .order_by(desc(ContextSnapshot.created_at))
                .first()
            )
            if not snap:
                return None
            return {
                "session_id": snap.session_id,
                "summary": snap.summary,
                "active_tasks": _loads(snap.active_tasks) or [],
                "key_decisions": _loads(snap.key_decisions) or [],
                "open_questions": _loads(snap.open_questions) or [],
                "mood_at_end": snap.mood_at_end,
                "topics_discussed": _loads(snap.topics_discussed) or [],
                "message_count": snap.message_count,
                "created_at": snap.created_at.isoformat() if snap.created_at else None,
            }

    # ══════════════════════════════════════════════════════════════════════════
    # Context Builder (برای تزریق به System Prompt)
    # ══════════════════════════════════════════════════════════════════════════

    def get_context_for_llm(self) -> str:
        """
        یک رشته فارسی می‌سازد که شامل وضعیت فعلی کاربر است.
        این رشته به system prompt اضافه می‌شود.
        """
        parts: List[str] = []

        # ── Persona ──
        persona = self.get_persona()
        if persona.get("preferred_name"):
            parts.append(f"نام کاربر: {persona['preferred_name']}")
        if persona.get("age"):
            parts.append(f"سن: {persona['age']}")
        if persona.get("occupation"):
            parts.append(f"شغل/حوزه: {persona['occupation']}")
        if persona.get("mbti"):
            parts.append(f"MBTI: {persona['mbti']}")

        # ── Daily State امروز ──
        ds = self.get_today_state()
        if ds:
            if ds.get("mood"):     parts.append(f"حال و هوا: {ds['mood']}")
            if ds.get("energy"):   parts.append(f"انرژی: {ds['energy']}")
            if ds.get("stress_level"): parts.append(f"استرس: {ds['stress_level']}")
            if ds.get("current_tasks"):
                tasks_list = ds["current_tasks"]
                task_texts = [
                    t["text"] if isinstance(t, dict) else str(t)
                    for t in tasks_list
                ]
                parts.append(f"وظایف امروز: {', '.join(task_texts)}")
            if ds.get("blockers"):
                blockers_list = ds["blockers"]
                blocker_texts = [
                    b["text"] if isinstance(b, dict) else str(b)
                    for b in blockers_list
                ]
                parts.append(f"موانع: {', '.join(blocker_texts)}")

        # ── Psychology ──
        psych = self.get_psychology()
        if psych.get("stress_triggers"):
            parts.append(f"محرک‌های استرس: {', '.join(psych['stress_triggers'][-3:])}")
        if psych.get("motivators"):
            parts.append(f"انگیزه‌دهنده‌ها: {', '.join(psych['motivators'][-3:])}")

        # ── اهداف فعال ──
        goals = self.get_active_goals()
        if goals:
            top = goals[:3]
            goals_str = " | ".join(
                f"{g['title']} ({g['progress_percent']:.0f}%)" for g in top
            )
            parts.append(f"اهداف فعال: {goals_str}")

        # ── رویدادهای اخیر ──
        recent_wins = self.get_recent_events(limit=2, event_type="win")
        if recent_wins:
            parts.append(f"موفقیت‌های اخیر: {', '.join(e['title'] for e in recent_wins)}")

        recent_setbacks = self.get_recent_events(limit=2, event_type="setback")
        if recent_setbacks:
            parts.append(f"چالش‌های اخیر: {', '.join(e['title'] for e in recent_setbacks)}")

        # ── Snapshot سشن قبلی ──
        snap = self.get_last_snapshot()
        if snap:
            parts.append(f"\n[خلاصه آخرین گفتگو]: {snap['summary']}")
            if snap.get("active_tasks"):
                parts.append(f"[تسک‌های باز از سشن قبل]: {', '.join(snap['active_tasks'])}")
            if snap.get("open_questions"):
                parts.append(f"[سؤال‌های باز]: {', '.join(snap['open_questions'])}")

        return "\n".join(parts) if parts else "حافظه‌ای ثبت نشده است."

    # ══════════════════════════════════════════════════════════════════════════
    # Legacy API (سازگاری با main.py فعلی)
    # ══════════════════════════════════════════════════════════════════════════

    def update_memory_fields(self, updates: Dict[str, Any]) -> None:
        """
        سازگار با memory_updater.apply_updates.
        فیلدها را بر اساس ساختار flat-dot به جداول مناسب map می‌کند.
        """
        daily = updates.get("daily_state", {})
        if daily:
            self.update_daily_state(
                mood=daily.get("mood"),
                energy=daily.get("energy"),
                stress_level=daily.get("stress_level"),
                current_tasks=daily.get("current_tasks"),
                blockers=daily.get("blockers"),
            )

        psych = updates.get("psychology", {})
        for field in ("stress_triggers", "motivators"):
            for item in psych.get(field, []):
                self.append_to_psychology_list(field, item)

        behavioral = updates.get("behavioral_memory", {})
        for item in behavioral.get("habits_positive", []):
            self.append_to_psychology_list("motivators", item)

        events = updates.get("events", {})
        for win in events.get("wins", []):
            self.add_event("win", title=win if isinstance(win, str) else str(win))
        for setback in events.get("setbacks", []):
            self.add_event("setback", title=setback if isinstance(setback, str) else str(setback))

        tasks = updates.get("task_history", {})
        for task in tasks.get("completed_tasks", []):
            self.add_event("task", title=task if isinstance(task, str) else str(task))

    @property
    def memory(self) -> Dict[str, Any]:
        """Legacy property - برای سازگاری با memory_updater.py"""
        return {
            "user_identity": self.get_persona(),
            "psychology": self.get_psychology(),
            "daily_state": self.get_today_state(),
            "events": {
                "wins": self.get_recent_events(5, "win"),
                "setbacks": self.get_recent_events(5, "setback"),
            },
            "task_history": {
                "completed_tasks": self.get_recent_events(10, "task"),
            },
        }
