"""
memory_manager.py - Jarvis-You (نسخه ۲)
مدیریت حافظه با SQLAlchemy - سازگار با SQLite و PostgreSQL
"""

from __future__ import annotations

import json
import uuid
<<<<<<< HEAD
from datetime import date, datetime, timedelta, timezone
=======
from datetime import date, datetime
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func

from database import (
<<<<<<< HEAD
    BeliefRevision,
=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    ContextSnapshot,
    Conversation,
    DailyState,
    EventTask,
    Goal,
    Habit,
    HabitLog,
    Persona,
    Psychology,
<<<<<<< HEAD
    TaskSlot,
    WorkTask,
    get_session,
)

MAX_HISTORY_FOR_LLM = 15  # فقط این تعداد پیام آخر به Gemini به‌عنوان context فرستاده می‌شه (نه کل ۱۰۰ تای UI) تا مصرف توکن هر پیام کنترل‌شده بمونه

IRAN_UTC_OFFSET = timedelta(hours=3, minutes=30)  # ایران DST نداره (از ۱۴۰۱ به بعد)، آفست همیشه ثابته


def _today_iran_str() -> str:
    """
    FIX (اختلاف UTC/ایران توی MemoryManager): این ماژول از main.py مستقل
    عمل می‌کنه و قبلاً مستقیم date.today() (ساعت سرور Vercel = UTC) رو توی
    update_daily_state / get_today_state / log_habit صدا می‌زد. نزدیک نیمه‌شب
    (۲۰:۳۰ تا ۰۰:۰۰ UTC، یعنی ۰۰:۰۰ تا ۰۳:۳۰ بامداد به وقت ایران) این باعث
    می‌شد رکوردها زیر تاریخ «دیروز» ثبت بشن. همون منطق آفست ثابت +۳:۳۰ که
    توی main.py هست، اینجا هم جدا پیاده‌سازی شده چون این فایل به main.py
    وابسته نیست (وگرنه import چرخه‌ای می‌شد).
    """
    return (datetime.now(timezone.utc) + IRAN_UTC_OFFSET).date().isoformat()
=======
    get_session,
    init_db,
)

MAX_HISTORY_FOR_LLM = 20
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9


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
<<<<<<< HEAD

    FIX (multi-user): این کلاس قبلاً global و singleton بود — یک instance
    برای کل سرور با یک `session_id` تصادفی که هیچ ارتباطی با "کاربر" نداشت.
    الان هر instance به یک `user_id` مشخص (از جدول users) متصل است و همه‌ی
    کوئری‌ها با `user_id=self.user_id` فیلتر می‌شوند. باید به‌ازای هر
    request یک instance جدید ساخته شود:
        mm = MemoryManager(user_id=current_user.id)
    نه یک‌بار در startup مثل قبل.

    `session_id` همچنان وجود دارد، اما فقط برای گروه‌بندی پیام‌های یک
    نشست چت (Conversation.session_id) استفاده می‌شود — نه برای هویت کاربر.
    """

    def __init__(self, user_id: int, session_id: Optional[str] = None) -> None:
        if not user_id:
            raise ValueError("MemoryManager requires a user_id")
        # FIX (bug #1 — DuplicatePreparedStatement crashes in production):
        # this used to call init_db() -> Base.metadata.create_all() on
        # *every* MemoryManager instantiation, and MemoryManager is
        # constructed at least once per chat request (often more, e.g.
        # scheduler_service's reflection check). On Vercel/Supabase with
        # PgBouncer in front, repeated create_all() calls on the same
        # pooled connection are exactly what triggers
        # `psycopg.errors.DuplicatePreparedStatement`. Schema creation only
        # needs to happen once at process startup — main.py already does
        # this (`init_db()` in its startup block, guarded by SKIP_DB_INIT).
        # Do NOT re-add an init_db() call here.
        self.user_id: int = user_id
=======
    هر instance یک session_id دارد که تاریخچه مکالمه جاری را نگه می‌دارد.
    """

    def __init__(self, session_id: Optional[str] = None) -> None:
        init_db()
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
        self.session_id: str = session_id or str(uuid.uuid4())
        self._ensure_singleton_rows()

    # ── Bootstrap ──────────────────────────────────────────────────────────────

    def _ensure_singleton_rows(self) -> None:
<<<<<<< HEAD
        """Persona و Psychology باید به‌ازای هر کاربر یک ردیف داشته باشند."""
        with get_session() as session:
            if not session.query(Persona).filter_by(user_id=self.user_id).first():
                session.add(Persona(user_id=self.user_id))
            if not session.query(Psychology).filter_by(user_id=self.user_id).first():
                session.add(Psychology(user_id=self.user_id))
=======
        """Persona و Psychology باید همیشه یک ردیف با id=1 داشته باشند."""
        with get_session() as session:
            if not session.get(Persona, 1):
                session.add(Persona(id=1))
            if not session.get(Psychology, 1):
                session.add(Psychology(id=1))
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
            session.commit()

    # ══════════════════════════════════════════════════════════════════════════
    # لایه ۱ - Static Memory
    # ══════════════════════════════════════════════════════════════════════════

    # ── Persona ────────────────────────────────────────────────────────────────

    def get_persona(self) -> Dict[str, Any]:
        with get_session() as session:
<<<<<<< HEAD
            p = session.query(Persona).filter_by(user_id=self.user_id).first()
=======
            p = session.get(Persona, 1)
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
<<<<<<< HEAD
            p = session.query(Persona).filter_by(user_id=self.user_id).first()
            if not p:
                p = Persona(user_id=self.user_id)
=======
            p = session.get(Persona, 1)
            if not p:
                p = Persona(id=1)
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
                session.add(p)
            for key, val in kwargs.items():
                if hasattr(p, key):
                    setattr(p, key, _dumps(val) if key in _json_fields else val)
            session.commit()

    # ── Psychology ─────────────────────────────────────────────────────────────

    def get_psychology(self) -> Dict[str, Any]:
        with get_session() as session:
<<<<<<< HEAD
            ps = session.query(Psychology).filter_by(user_id=self.user_id).first()
=======
            ps = session.get(Psychology, 1)
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
<<<<<<< HEAD
            ps = session.query(Psychology).filter_by(user_id=self.user_id).first()
=======
            ps = session.get(Psychology, 1)
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
<<<<<<< HEAD
            ps = session.query(Psychology).filter_by(user_id=self.user_id).first()
=======
            ps = session.get(Psychology, 1)
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
            if not ps:
                return
            for key, val in kwargs.items():
                if hasattr(ps, key):
                    setattr(ps, key, _dumps(val) if key in _json_fields else val)
            session.commit()

<<<<<<< HEAD
    # ── Behavioral reflection (cognitive scaffolding) ────────────────────────
    # این بخش دقیقاً همون نقطه‌کوری رو هدف می‌گیره که خودآگاهی (خوداظهاری در
    # onboarding و چت) هیچوقت با رفتار واقعی سنجیده نمی‌شه. اینجا داده‌ی
    # عینی (نرخ تکمیل تسک، رهاکردن پروژه، رکود اهداف) رو با پروفایل
    # روان‌شناختی self-reported مقایسه می‌کنه.

    def compute_behavior_snapshot(self, lookback_days: int = 14) -> Dict[str, Any]:
        """
        آمار رفتاری عینی رو از داده‌ی واقعی (نه خوداظهاری) محاسبه می‌کنه:
        - نرخ تکمیل تسک‌های روزانه
        - تعداد WorkTaskهایی که شروع شدن ولی رها موندن (نه completed، نه cancelled)
        - تعداد اهدافی که فعال‌ان ولی پیشرفت واقعی ناچیزی دارن (رکود)
        """
        with get_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=lookback_days)
            cutoff_date = cutoff.date().isoformat()

            # FIX (معماری): قبلاً این آمار از DailyState.current_tasks
            # می‌اومد که خودش فقط یک حدسِ LLM از روی متن چت بود — یعنی
            # «نرخ تکمیل» واقعاً نرخ تکمیلِ چیزی نبود که کاربر رو صفحه‌ی
            # Daily تیک می‌زد. حالا مستقیم از TaskSlot (همون منبعی که
            # صفحه‌ی Daily/Weekly می‌خونه) محاسبه می‌شه.
            task_rows = (
                session.query(TaskSlot)
                .filter(TaskSlot.user_id == self.user_id, TaskSlot.date >= cutoff_date)
                .all()
            )
            total_tasks = len(task_rows)
            completed_tasks = sum(1 for t in task_rows if t.completed)
            completion_rate = (completed_tasks / total_tasks) if total_tasks else None

            states = (
                session.query(DailyState)
                .filter(DailyState.user_id == self.user_id, DailyState.created_at >= cutoff)
                .all()
            )

            stale_cutoff = datetime.utcnow() - timedelta(days=10)
            abandoned_tasks = (
                session.query(WorkTask)
                .filter(
                    WorkTask.user_id == self.user_id,
                    WorkTask.status.in_(["pending", "in_progress"]),
                    WorkTask.created_at < stale_cutoff,
                )
                .count()
            )

            stagnant_goals = (
                session.query(Goal)
                .filter(
                    Goal.user_id == self.user_id,
                    Goal.status == "active",
                    Goal.updated_at < stale_cutoff,
                    Goal.progress_percent < 30,
                )
                .count()
            )

            enough_data = len(states) >= 5 or abandoned_tasks + stagnant_goals >= 2

            return {
                "completion_rate": completion_rate,
                "abandoned_tasks": abandoned_tasks,
                "stagnant_goals": stagnant_goals,
                "sample_days": len(states),
                "enough_data": enough_data,
            }

    def check_and_generate_reflection(self, min_days_between_checks: int = 7, llm_client=None) -> Optional[str]:
        """
        این متد رو scheduler_service.py به‌صورت دوره‌ای صدا می‌زنه (نه main.py
        مستقیم). اگه:
          1) به‌اندازه‌ی کافی از آخرین چک گذشته باشه،
          2) داده‌ی رفتاری کافی جمع شده باشه،
          3) و بین رفتار عینی و پروفایل self-reported تناقض معناداری باشه،
        یک سوال بازتابی کوتاه توی Psychology.pending_reflection ذخیره می‌کنه.
        این سوال یک‌بار (دفعه‌ی بعدی چت) توسط main.py خونده، به کاربر نشون
        داده، و بلافاصله پاک می‌شه — یعنی هر تناقض فقط یک‌بار مطرح می‌شه، نه
        سرکوفت مکرر.

        اگه llm_client داده بشه، اول سعی می‌کنه با LLM (memory_updater.
        detect_behavioral_reflection) تشخیص بده — چون می‌تونه الگوهای
        ظریف‌تر و ترکیبی رو ببینه، نه فقط چند تا آستانه‌ی عددی ثابت. اگه
        llm_client داده نشه، یا LLM خطا بده/چیزی برنگردونه، fallback می‌کنه
        به قوانین آماری ساده‌ی `_diff_self_report_vs_behavior` که رایگان و
        همیشه در دسترسه.

        برمی‌گردونه: متن سوال (اگه ساخته شد) یا None.
        """
        with get_session() as session:
            ps = session.query(Psychology).filter_by(user_id=self.user_id).first()
            if not ps:
                return None

            if ps.pending_reflection:
                return None  # یه سوال از قبل معلقه، تا جواب داده نشه سوال جدید نمی‌سازیم

            if ps.last_reflection_check:
                days_since = (datetime.utcnow() - ps.last_reflection_check).days
                if days_since < min_days_between_checks:
                    return None

            ps.last_reflection_check = datetime.utcnow()
            session.commit()

            snapshot = self.compute_behavior_snapshot()
            if not snapshot["enough_data"]:
                return None

            self_reported_patterns = _loads(ps.procrastination_patterns) or []

            reflection_text = None
            if llm_client is not None:
                psychology_profile = {
                    "stress_triggers": _loads(ps.stress_triggers) or [],
                    "motivators": _loads(ps.motivators) or [],
                    "fear_patterns": _loads(ps.fear_patterns) or [],
                    "procrastination_patterns": self_reported_patterns,
                    "communication_style": ps.communication_style,
                    "decision_making_style": ps.decision_making_style,
                }
                try:
                    from memory_updater import detect_behavioral_reflection
                    reflection_text = detect_behavioral_reflection(
                        client=llm_client,
                        psychology_profile=psychology_profile,
                        behavior_snapshot=snapshot,
                    )
                except Exception as e:
                    print(f"⚠️ LLM reflection detection failed, using rule-based fallback: {e}")
                    reflection_text = None

            if not reflection_text:
                # fallback: قوانین آماری ساده (رایگان، همیشه در دسترس)
                reflection_text = self._diff_self_report_vs_behavior(self_reported_patterns, snapshot)

            if reflection_text:
                ps.pending_reflection = reflection_text
                session.commit()

            return reflection_text

    @staticmethod
    def _diff_self_report_vs_behavior(
        self_reported_patterns: List[str], snapshot: Dict[str, Any]
    ) -> Optional[str]:
        """
        منطق مقایسه — عمداً ساده و قابل‌توضیحه (نه یک مدل جعبه‌سیاه):
        اگه رفتار عینی نشونه‌ی روشنی از یه الگو (رهاکردن، نرخ تکمیل پایین)
        داره که هنوز توی خوداظهاری کاربر ثبت نشده، یک سوال بازتابی می‌سازه.
        عمداً محافظه‌کارانه‌ست: فقط وقتی سیگنال قوی و مکرره مطرح می‌کنه، نه
        هر نوسان کوچیک.
        """
        already_aware = any(
            kw in " ".join(self_reported_patterns) for kw in ["رهاکردن", "رها کردن", "ول کردن"]
        )
        if snapshot["abandoned_tasks"] >= 2 and not already_aware:
            return (
                f"توی {snapshot['abandoned_tasks']} تا از پروژه‌های اخیرت، شروع کردی ولی "
                "بیش از ۱۰ روزه که بی‌حرکت موندن. این با چیزی که قبلاً درباره‌ی سبک "
                "کاریت گفته بودی هم‌خونی نداره — می‌خوای باهم ببینیم واقعاً چی باعث "
                "این توقف‌ها می‌شه؟"
            )

        if (
            snapshot["completion_rate"] is not None
            and snapshot["completion_rate"] < 0.35
            and snapshot["sample_days"] >= 7
        ):
            return (
                f"توی {snapshot['sample_days']} روز اخیر، حدود "
                f"{int(snapshot['completion_rate'] * 100)}٪ از تسک‌های روزانه‌ت تکمیل شدن. "
                "می‌خوام بدونم این به‌خاطر زیاد بودن حجم تسک‌هاست یا یه چیز دیگه داره "
                "جلوتو می‌گیره؟"
            )

        if snapshot["stagnant_goals"] >= 2:
            return (
                f"{snapshot['stagnant_goals']} تا از هدف‌های فعالت بیش از ۱۰ روزه پیشرفت "
                "محسوسی نداشتن. می‌خوای باهم بررسی کنیم که هنوز برات اولویتن یا وقتشه "
                "بازنگری‌شون کنیم؟"
            )

        return None

    def consume_pending_reflection(self) -> Optional[str]:
        """
        main.py این رو توی هر چت صدا می‌زنه. اگه سوال معلقی هست، متنش رو
        برمی‌گردونه و پاک می‌کنه (یعنی فقط یک‌بار پرسیده می‌شه) — ولی قبلش
        `awaiting_reflection_reply_since` و `last_reflection_text` رو ست
        می‌کنه، تا پیام *بعدی* کاربر به‌عنوان جواب احتمالی به همین سوال در
        نظر گرفته بشه (نگاه کن به `check_belief_revision`).
        """
        with get_session() as session:
            ps = session.query(Psychology).filter_by(user_id=self.user_id).first()
            if not ps or not ps.pending_reflection:
                return None
            text = ps.pending_reflection
            ps.pending_reflection = None
            ps.awaiting_reflection_reply_since = datetime.utcnow()
            ps.last_reflection_text = text
            session.commit()
            return text

    def check_belief_revision(self, user_message: str, llm_client=None) -> Optional[dict]:
        """
        لایه‌ی ۵ داربست شناختی (حلقه‌ی بسته). main.py این رو *قبل* از
        پردازش هر پیام کاربر صدا می‌زنه. اگه اخیراً یه سوال بازتابی مطرح
        شده بود (awaiting_reflection_reply_since ست شده)، پیام فعلی کاربر
        رو به‌عنوان جواب احتمالی بررسی می‌کنه.

        اگه واقعاً یه اصلاح باور تشخیص داده بشه:
          - یه ردیف جدید توی BeliefRevision ثبت می‌شه (تاریخچه، نه overwrite)
          - خودِ فیلد Psychology هم به‌روزرسانی می‌شه (باور فعلی)
        این پنجره‌ی "منتظر جواب" فقط برای *یک* پیام بعدی بازه — بعدش پاک
        می‌شه، چون نمی‌خوایم هر پیام بعدی رو (حتی بی‌ربط) به‌عنوان جواب به
        یه سوال قدیمی تفسیر کنیم.

        برمی‌گردونه: dict خلاصه‌ی تغییر (اگه ثبت شد) یا None.
        """
        if llm_client is None:
            return None

        with get_session() as session:
            ps = session.query(Psychology).filter_by(user_id=self.user_id).first()
            if not ps or not ps.awaiting_reflection_reply_since or not ps.last_reflection_text:
                return None

            # پنجره فقط یک پیام بعدیه — همیشه بعد از این چک پاک می‌شه،
            # چه تغییری تشخیص داده بشه چه نه.
            reflection_question = ps.last_reflection_text
            ps.awaiting_reflection_reply_since = None
            ps.last_reflection_text = None
            session.commit()

            current_psychology = {
                "stress_triggers": _loads(ps.stress_triggers) or [],
                "motivators": _loads(ps.motivators) or [],
                "fear_patterns": _loads(ps.fear_patterns) or [],
                "procrastination_patterns": _loads(ps.procrastination_patterns) or [],
                "communication_style": ps.communication_style,
                "decision_making_style": ps.decision_making_style,
            }

            try:
                from memory_updater import extract_belief_revision
                revision = extract_belief_revision(
                    client=llm_client,
                    reflection_question=reflection_question,
                    user_reply=user_message,
                    current_psychology=current_psychology,
                )
            except Exception as e:
                print(f"⚠️ belief revision check failed: {e}")
                return None

            if not revision:
                return None

            field_name = revision.get("field_name")
            new_value = revision.get("new_value", "")
            old_value_summary = revision.get("old_value_summary", "")
            confidence = revision.get("confidence", "medium")

            # فقط به فیلدهای شناخته‌شده اجازه بده — امنیت/سلامت داده
            _json_fields = {"stress_triggers", "motivators", "fear_patterns", "procrastination_patterns"}
            _string_fields = {"communication_style", "decision_making_style"}
            if field_name not in _json_fields and field_name not in _string_fields:
                return None

            session.add(BeliefRevision(
                user_id=self.user_id,
                field_name=field_name,
                old_value=old_value_summary,
                new_value=new_value,
                trigger_reflection=reflection_question,
                user_reply=user_message[:1000],
                confidence=confidence,
            ))

            # باور فعلی رو هم به‌روز می‌کنیم — ولی فقط اگه confidence پایین نباشه
            if confidence in ("medium", "high"):
                if field_name in _json_fields:
                    setattr(ps, field_name, _dumps([new_value]))
                else:
                    setattr(ps, field_name, new_value)

            session.commit()

            return {
                "field_name": field_name,
                "old_value": old_value_summary,
                "new_value": new_value,
                "confidence": confidence,
            }

    def get_belief_revision_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """تاریخچه‌ی کامل تغییر باورها برای این کاربر — برای نمایش در UI یا تحلیل."""
        with get_session() as session:
            rows = (
                session.query(BeliefRevision)
                .filter(BeliefRevision.user_id == self.user_id)
                .order_by(desc(BeliefRevision.created_at))
                .limit(limit)
                .all()
            )
            return [
                {
                    "field_name": r.field_name,
                    "old_value": r.old_value,
                    "new_value": r.new_value,
                    "confidence": r.confidence,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]

=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
<<<<<<< HEAD
                user_id=self.user_id,
=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
<<<<<<< HEAD
                .filter(Goal.user_id == self.user_id, Goal.status == "active")
=======
                .filter(Goal.status == "active")
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
<<<<<<< HEAD
            if g and g.user_id != self.user_id:
                return  # not this user's goal
=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
<<<<<<< HEAD
        today = _today_iran_str()
        with get_session() as session:
            ds = session.query(DailyState).filter_by(user_id=self.user_id, date=today).first()
            if not ds:
                ds = DailyState(user_id=self.user_id, date=today)
=======
        today = date.today().isoformat()
        with get_session() as session:
            ds = session.query(DailyState).filter_by(date=today).first()
            if not ds:
                ds = DailyState(date=today)
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
<<<<<<< HEAD
        today = _today_iran_str()
        with get_session() as session:
            ds = session.query(DailyState).filter_by(user_id=self.user_id, date=today).first()
=======
        today = date.today().isoformat()
        with get_session() as session:
            ds = session.query(DailyState).filter_by(date=today).first()
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
<<<<<<< HEAD
                .filter(DailyState.user_id == self.user_id)
=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
                .order_by(desc(DailyState.date))
                .limit(days)
                .all()
            )
            return [
                {
                    "date": r.date, "mood": r.mood, "energy": r.energy,
                    "stress_level": r.stress_level,
<<<<<<< HEAD
=======
                    "current_tasks": _loads(r.current_tasks) or [],
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
                }
                for r in reversed(rows)
            ]

<<<<<<< HEAD
    # ── Tasks (منبع حقیقت = TaskSlot، نه DailyState.current_tasks) ─────────────
    # FIX (معماری): قبلاً «تسک‌های امروز» که به مدل تزریق می‌شد از
    # DailyState.current_tasks می‌آمد — ستونی که فقط با یک LLM extraction
    # جدا (memory_updater.extract_memory_updates) پر می‌شد و هیچ ربطی به
    # چیزی که کاربر واقعاً در صفحه‌ی Daily/Weekly می‌بیند نداشت. این دو
    # حافظه‌ی مستقل، دقیقاً همون چیزی بود که باعث می‌شد جارویس تو چت یک
    # چیز فکر کنه و صفحه‌ی Daily چیز دیگه نشون بده. حالا هر دو از یک جدول
    # (TaskSlot، در main.py هم استفاده می‌شود) می‌خوانند.
    def get_today_tasks(self) -> List[Dict[str, Any]]:
        today = _today_iran_str()
        with get_session() as session:
            rows = (
                session.query(TaskSlot)
                .filter(TaskSlot.user_id == self.user_id, TaskSlot.date == today)
                .order_by(TaskSlot.hour)
                .all()
            )
            return [{"text": r.text, "completed": bool(r.completed), "hour": r.hour} for r in rows]

=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
<<<<<<< HEAD
                user_id=self.user_id,
=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
<<<<<<< HEAD
            q = session.query(EventTask).filter(EventTask.user_id == self.user_id).order_by(desc(EventTask.occurred_at))
=======
            q = session.query(EventTask).order_by(desc(EventTask.occurred_at))
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
<<<<<<< HEAD
                user_id=self.user_id,
=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
<<<<<<< HEAD
        today = _today_iran_str()
        with get_session() as session:
            log = HabitLog(
                user_id=self.user_id,
=======
        today = date.today().isoformat()
        with get_session() as session:
            log = HabitLog(
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
<<<<<<< HEAD
            if habit and habit.user_id != self.user_id:
                habit = None  # not this user's habit
=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
<<<<<<< HEAD
            habits = session.query(Habit).filter_by(user_id=self.user_id, is_active=True).all()
=======
            habits = session.query(Habit).filter_by(is_active=True).all()
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
<<<<<<< HEAD
                    user_id=self.user_id,
=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
                    session_id=self.session_id,
                    role="user",
                    content=user_message,
                    model_used=model_used,
                ),
                Conversation(
<<<<<<< HEAD
                    user_id=self.user_id,
=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
<<<<<<< HEAD
                .filter(Conversation.user_id == self.user_id)
=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
                .order_by(desc(Conversation.id))
                .limit(limit)
                .all()
            )
            return [{"role": r.role, "content": r.content} for r in reversed(rows)]

    def get_all_conversations(self) -> List[Dict[str, Any]]:
        with get_session() as session:
<<<<<<< HEAD
            rows = (
                session.query(Conversation)
                .filter(Conversation.user_id == self.user_id)
                .order_by(Conversation.id)
                .all()
            )
=======
            rows = session.query(Conversation).order_by(Conversation.id).all()
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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

<<<<<<< HEAD
    def get_recent_conversations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        برای صفحه‌ی چت: آخرین `limit` پیام (پیش‌فرض ۱۰۰) رو برمی‌گردونه تا
        کاربر با باز کردن دوباره‌ی تب چت، مکالمه‌ی قبلی‌اش رو ببینه — نه یه
        چت خالی. این جدا از `get_conversation_history` هست که فقط
        MAX_HISTORY_FOR_LLM (۱۰ تا ۱۵ پیام) رو برای context دادن به Gemini
        برمی‌گردونه.
        """
        with get_session() as session:
            rows = (
                session.query(Conversation)
                .filter(Conversation.user_id == self.user_id)
                .order_by(desc(Conversation.id))
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": r.id,
                    "session_id": r.session_id,
                    "role": r.role,
                    "content": r.content,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in reversed(rows)
            ]

=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
<<<<<<< HEAD
                .filter_by(user_id=self.user_id, session_id=self.session_id)
=======
                .filter_by(session_id=self.session_id)
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
                .scalar()
                or 0
            )
            snap = ContextSnapshot(
<<<<<<< HEAD
                user_id=self.user_id,
=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
<<<<<<< HEAD
                .filter(
                    ContextSnapshot.user_id == self.user_id,
                    ContextSnapshot.session_id != self.session_id,
                )
=======
                .filter(ContextSnapshot.session_id != self.session_id)
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
<<<<<<< HEAD
        این رشته به system prompt اضافه می‌شود — یعنی این تابع سر هر پیامِ
        چت صدا زده می‌شه.

        FIX (کندی): نسخه‌ی قبلی این تابع، ۷ متد جدا (get_persona،
        get_today_state، get_psychology، get_active_goals،
        get_recent_events ×۲، get_last_snapshot) را صدا می‌زد و هرکدوم
        `with get_session()` خودشو باز/بسته می‌کرد — یعنی فقط برای ساخت
        همین یک رشته، ۷-۸ تا session/connection جدا به دیتابیس باز می‌شد.
        روی هاستِ serverless (NullPool، بدون pool گرم) این یعنی ۷-۸ تا
        handshake جدا با Supabase، سر *هر* پیام چت. الان همه‌چی داخل یک
        `with get_session()` واحد جمع شده — همون کوئری‌ها، ولی یک session.
        """
        with get_session() as session:
            parts: List[str] = []
            today = _today_iran_str()

            # ── Persona ──
            p = session.query(Persona).filter_by(user_id=self.user_id).first()
            if p:
                if p.preferred_name:
                    parts.append(f"نام کاربر: {p.preferred_name}")
                if p.age:
                    parts.append(f"سن: {p.age}")
                if p.occupation:
                    parts.append(f"شغل/حوزه: {p.occupation}")
                if p.mbti:
                    parts.append(f"MBTI: {p.mbti}")

            # ── Daily State امروز (mood/energy/stress/blockers — نه تسک‌ها) ──
            ds = session.query(DailyState).filter_by(user_id=self.user_id, date=today).first()
            if ds:
                if ds.mood:
                    parts.append(f"حال و هوا: {ds.mood}")
                if ds.energy:
                    parts.append(f"انرژی: {ds.energy}")
                if ds.stress_level:
                    parts.append(f"استرس: {ds.stress_level}")
                blockers_list = _loads(ds.blockers) or []
                if blockers_list:
                    blocker_texts = [b["text"] if isinstance(b, dict) else str(b) for b in blockers_list]
                    parts.append(f"موانع: {', '.join(blocker_texts)}")

            # ── تسک‌های امروز — از TaskSlot، یعنی همون منبعی که صفحه‌ی
            #    Daily/Weekly نشون می‌ده (نه یک کپی مجزای LLM-guessed) ──
            task_rows = (
                session.query(TaskSlot)
                .filter(TaskSlot.user_id == self.user_id, TaskSlot.date == today)
                .order_by(TaskSlot.hour)
                .all()
            )
            if task_rows:
                task_lines = [
                    f"• {t.text} [{'✅ تکمیل‌شده' if t.completed else '⏳ در حال انجام'}]"
                    for t in task_rows
                ]
                parts.append("وضعیت وظایف امروز کاربر:\n" + "\n".join(task_lines))

            # ── Psychology ──
            psych = session.query(Psychology).filter_by(user_id=self.user_id).first()
            if psych:
                stress_triggers = _loads(psych.stress_triggers) or []
                if stress_triggers:
                    parts.append(f"محرک‌های استرس: {', '.join(stress_triggers[-3:])}")
                motivators = _loads(psych.motivators) or []
                if motivators:
                    parts.append(f"انگیزه‌دهنده‌ها: {', '.join(motivators[-3:])}")

            # ── اهداف فعال ──
            goals = (
                session.query(Goal)
                .filter(Goal.user_id == self.user_id, Goal.status == "active")
                .order_by(Goal.priority)
                .limit(3)
                .all()
            )
            if goals:
                goals_str = " | ".join(f"{g.title} ({g.progress_percent:.0f}%)" for g in goals)
                parts.append(f"اهداف فعال: {goals_str}")

            # ── رویدادهای اخیر ──
            recent_wins = (
                session.query(EventTask)
                .filter(EventTask.user_id == self.user_id, EventTask.event_type == "win")
                .order_by(desc(EventTask.occurred_at))
                .limit(2)
                .all()
            )
            if recent_wins:
                parts.append(f"موفقیت‌های اخیر: {', '.join(e.title for e in recent_wins)}")

            recent_setbacks = (
                session.query(EventTask)
                .filter(EventTask.user_id == self.user_id, EventTask.event_type == "setback")
                .order_by(desc(EventTask.occurred_at))
                .limit(2)
                .all()
            )
            if recent_setbacks:
                parts.append(f"چالش‌های اخیر: {', '.join(e.title for e in recent_setbacks)}")

            # ── Snapshot سشن قبلی ──
            snap = (
                session.query(ContextSnapshot)
                .filter(
                    ContextSnapshot.user_id == self.user_id,
                    ContextSnapshot.session_id != self.session_id,
                )
                .order_by(desc(ContextSnapshot.created_at))
                .first()
            )
            if snap:
                parts.append(f"\n[خلاصه آخرین گفتگو]: {snap.summary}")
                active_tasks = _loads(snap.active_tasks) or []
                if active_tasks:
                    parts.append(f"[تسک‌های باز از سشن قبل]: {', '.join(active_tasks)}")
                open_questions = _loads(snap.open_questions) or []
                if open_questions:
                    parts.append(f"[سؤال‌های باز]: {', '.join(open_questions)}")

            return "\n".join(parts) if parts else "حافظه‌ای ثبت نشده است."
=======
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
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9

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
<<<<<<< HEAD
            # FIX (معماری): "current_tasks" دیگر از این مسیر نوشته نمی‌شود.
            # این مسیر یک LLM جدا و مستقل (memory_updater.extract_memory_updates)
            # بود که از روی متن آزاد چت حدس می‌زد کاربر چه تسک‌هایی دارد —
            # کاملاً جدا از TaskSlot (منبع واقعی‌ای که چت/smart-planner و
            # صفحات Daily/Weekly هر دو رویش می‌نویسند). نگه‌داشتن این مسیر
            # یعنی دو "حقیقت" مستقل برای یک مفهوم، که دقیقاً علت ناهماهنگیِ
            # قبلی بین چت و صفحه‌ی Daily بود.
=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
            self.update_daily_state(
                mood=daily.get("mood"),
                energy=daily.get("energy"),
                stress_level=daily.get("stress_level"),
<<<<<<< HEAD
=======
                current_tasks=daily.get("current_tasks"),
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
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
