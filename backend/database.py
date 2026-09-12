import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

# -----------------------------------------------------------------------------
# Database URL / Engine
# -----------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./jarvis.db")

# Normalize legacy/ambiguous Postgres URL schemes so we always end up on the
# psycopg3 driver ("postgresql+psycopg://"), which is what's installed via
# `psycopg[binary]` in requirements.txt:
# - "postgres://"     -> legacy scheme some providers (old Heroku-style URLs) still emit
# - "postgresql://"   -> no explicit driver, SQLAlchemy would default to psycopg2
#                         (not installed) instead of psycopg3
# Supabase connection strings can be used as-is (postgresql://...) or with the
# driver already specified (postgresql+psycopg://...) — both are handled below.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

_IS_SQLITE = DATABASE_URL.startswith("sqlite")
_IS_POSTGRES = DATABASE_URL.startswith("postgresql")

# FIX (Vercel/Supabase migration): Supabase enforces a hard cap on concurrent
# Postgres connections. A traditional SQLAlchemy QueuePool holds connections
# open for the lifetime of a worker process; on Vercel Serverless every
# invocation may run in a brand-new process, so pooled connections pile up
# across cold starts and exhaust Supabase's connection limit within minutes.
# `VERCEL` is set automatically by the Vercel runtime (no config needed on
# our end) — when detected (or when explicitly requested via
# DB_POOL_MODE=nullpool, for other serverless/edge hosts), every request
# opens and tears down its own connection instead of keeping one warm.
_IS_SERVERLESS = bool(os.getenv("VERCEL")) or os.getenv("DB_POOL_MODE", "").strip().lower() == "nullpool"

_engine_kwargs: dict = {"echo": False, "future": True, "pool_pre_ping": True}
if _IS_POSTGRES:
    # FIX: psycopg3 caches server-side prepared statements by default.
    # Supabase's connection pooler (PgBouncer, transaction pooling mode)
    # does not support prepared statements persisting across transactions —
    # a connection handed to one request may still have another request's
    # prepared statement cached, causing
    # `psycopg.errors.DuplicatePreparedStatement: prepared statement "_pg3_0"
    # already exists`. This is especially visible on serverless (Vercel),
    # where connections get reused/interleaved unpredictably across
    # invocations. Disabling server-side prepare entirely avoids it.
    _engine_kwargs["connect_args"] = {"prepare_threshold": None}

if _IS_POSTGRES and _IS_SERVERLESS:
    _engine_kwargs["poolclass"] = NullPool
elif _IS_POSTGRES:
    # Traditional long-running server (Liara, a VM, Docker, plain uvicorn) —
    # a small persistent pool is fine and cheaper than reconnecting per request.
    _engine_kwargs["pool_size"] = 5
    _engine_kwargs["max_overflow"] = 10

engine = create_engine(DATABASE_URL, **_engine_kwargs)

# SQLite pragmas for better integrity/concurrency
if _IS_SQLITE:

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
        finally:
            cursor.close()


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# -----------------------------------------------------------------------------
# Base
# -----------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


def _json_col(nullable=True, default=None):
    """
    Cross-database JSON column helper:
    - PostgreSQL -> JSONB
    - SQLite -> Text (store serialized JSON string)
    """
    if _IS_POSTGRES:
        return Column(JSONB, nullable=nullable, default=default)

    # SQLite: default باید JSON string باشد، نه Python object
    if default is list:
        sqlite_default = "[]"
    elif default is dict:
        sqlite_default = "{}"
    elif default is None:
        sqlite_default = None
    else:
        sqlite_default = default

    return Column(Text, nullable=nullable, default=sqlite_default)


# -----------------------------------------------------------------------------
# Cross-database JSON (de)serialization helpers
# -----------------------------------------------------------------------------
# `_json_col()` columns are JSONB on PostgreSQL (already parsed/serialized by
# SQLAlchemy) and Text on SQLite (raw JSON strings). Every call site that reads
# or writes one of these columns must go through the helpers below instead of
# calling `json.dumps`/`json.loads` directly, otherwise PostgreSQL ends up with
# a JSON *string* stored inside a JSONB column instead of a real JSON object.


def json_load_from_db(value):
    """Deserialize a value read from a `_json_col()` column into a Python object.

    - PostgreSQL (JSONB): SQLAlchemy already returns a parsed Python object.
    - SQLite (Text): the raw JSON string is parsed here.
    """
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    return value


def json_dump_for_db(value):
    """Serialize a Python object for storage in a `_json_col()` column.

    - PostgreSQL (JSONB): SQLAlchemy handles serialization automatically, so
      the Python object is returned unchanged.
    - SQLite (Text): the object is dumped to a JSON string.
    """
    if value is None:
        return None
    if _IS_POSTGRES:
        return value
    return json.dumps(value, ensure_ascii=False)


# -----------------------------------------------------------------------------
# Session helpers
# -----------------------------------------------------------------------------


class _SessionWrapper:
    """
    Wraps a SQLAlchemy Session so it works both as a plain object
    (session = get_session()) and as a context manager
    (with get_session() as session:).
    """

    def __init__(self, session):
        self._session = session

    def __getattr__(self, name):
        return getattr(self._session, name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                self._session.rollback()
        finally:
            self._session.close()
        return False  # don't suppress exceptions


def get_session():
    """
    Returns a _SessionWrapper that can be used either as:
        session = get_session()          # manual close
        with get_session() as session:   # auto-close / rollback
    """
    return _SessionWrapper(SessionLocal())


# -----------------------------------------------------------------------------
# User (multi-user auth)
# -----------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    # FIX (multi-user): tracks whether the onboarding wizard has been completed,
    # so the frontend knows whether to route a fresh signup to /onboarding.
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # ── Password-reset & email-verification tokens (SECURITY) ────────────────
    # SECURITY: در reset_password_token فقط هشِ SHA-256 توکن ذخیره می‌شود، نه
    # خود توکن — تا لو رفتن دیتابیس هم به مهاجم توکن قابل استفاده ندهد.
    # پس از استفاده هر دو فیلد null می‌شوند (single-use / invalidation after use).
    reset_password_token = Column(String(255), nullable=True, index=True)
    reset_password_expires_at = Column(DateTime, nullable=True)  # UTC naive — مثل بقیه‌ی ستون‌ها

    verification_token_hash = Column(String(64), nullable=True, index=True)
    verification_token_expires = Column(DateTime, nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)


# -----------------------------------------------------------------------------
# Existing Models
# -----------------------------------------------------------------------------
class Persona(Base):
    __tablename__ = "persona"

    # FIX (multi-user): was `id = Column(Integer, primary_key=True, default=1)`,
    # a hardcoded singleton row shared by the whole app. Now one row per user.
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True,
        nullable=False, index=True,
    )
    preferred_name = Column(String(100), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(50), nullable=True)
    location = Column(String(200), nullable=True)
    occupation = Column(String(200), nullable=True)
    education_level = Column(String(200), nullable=True)
    languages = _json_col(nullable=True, default=list)
    core_values = _json_col(nullable=True, default=list)
    life_philosophy = Column(Text, nullable=True)
    mbti = Column(String(10), nullable=True)
    enneagram = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Psychology(Base):
    __tablename__ = "psychology"

    # FIX (multi-user): same singleton -> per-user change as Persona above.
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True,
        nullable=False, index=True,
    )
    stress_triggers = _json_col(nullable=True, default=list)
    motivators = _json_col(nullable=True, default=list)
    fear_patterns = _json_col(nullable=True, default=list)
    cognitive_biases = _json_col(nullable=True, default=list)
    coping_strategies = _json_col(nullable=True, default=list)
    attachment_style = Column(String(100), nullable=True)
    communication_style = Column(String(100), nullable=True)
    decision_making_style = Column(String(100), nullable=True)
    procrastination_patterns = _json_col(nullable=True, default=list)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Behavioral reflection (cognitive scaffolding) ───────────────────────
    # این دو فیلد اضافه شدن که پروفایل خوداظهاری (بالا) دیگه صرفاً append-only
    # نباشه. یک job دوره‌ای (scheduler_service.py) رفتار واقعی کاربر رو
    # (نرخ تکمیل تسک، رهاکردن پروژه‌ها، رکود اهداف) با همین فیلدهای بالا
    # (stress_triggers, procrastination_patterns, ...) می‌سنجه. اگه تناقض
    # معناداری پیدا کنه، یک سوال بازتابی کوتاه اینجا ذخیره می‌شه تا دفعه‌ی
    # بعد که کاربر چت کرد، جارویس طبیعی مطرحش کنه — نه هر پیام، فقط یک‌بار.
    last_reflection_check = Column(DateTime, nullable=True)
    pending_reflection = Column(Text, nullable=True)
    # وقتی یه reflection توی چت مصرف/نشون داده می‌شه، این ست می‌شه — یعنی
    # «منتظر جواب کاربر به این سوال بازتابی‌ایم». main.py پیام بعدی کاربر رو
    # به‌عنوان جواب احتمالی به همین سوال بررسی می‌کنه و اگه واقعاً باوری رو
    # اصلاح کرد، توی BeliefRevision لاگ می‌شه و پاک می‌شه.
    awaiting_reflection_reply_since = Column(DateTime, nullable=True)
    last_reflection_text = Column(Text, nullable=True)


class BeliefRevision(Base):
    """
    لایه‌ی ۵ داربست شناختی: حلقه‌ی بسته‌ی بازنویسی باور.
    برخلاف Psychology (که فقط وضعیت *فعلی* باور رو نگه می‌داره)، این جدول
    *تاریخچه‌ی تغییر* باورها رو ثبت می‌کنه — یعنی می‌شه دید یه باور
    self-reported کِی و چرا و به چه چیزی تغییر کرد. هیچ ردیفی حذف یا
    overwrite نمی‌شه؛ هر تغییر یه ردیف جدیده.
    """
    __tablename__ = "belief_revisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)  # مثلاً procrastination_patterns
    old_value = Column(Text, nullable=True)  # خلاصه‌ی باور قبلی
    new_value = Column(Text, nullable=True)  # خلاصه‌ی باور جدید
    trigger_reflection = Column(Text, nullable=True)  # سوالی که این تغییر رو برانگیخت
    user_reply = Column(Text, nullable=True)  # عین جواب کاربر
    confidence = Column(String(20), nullable=True)  # low / medium / high — چقدر LLM مطمئنه این واقعاً یه تغییر باوره
    created_at = Column(DateTime, default=datetime.utcnow)


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    priority = Column(Integer, default=5)
    timeframe = Column(String(50), nullable=True)
    target_date = Column(DateTime, nullable=True)
    milestones = _json_col(nullable=True, default=list)
    progress_percent = Column(Float, default=0.0)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DailyState(Base):
    __tablename__ = "daily_states"

    # FIX: the previous version of this file dropped `current_tasks` with a
    # comment claiming it had been migrated to WorkTask. It hadn't — main.py
    # and memory_manager.py both still read/write `state.current_tasks` and
    # `DailyState(..., current_tasks=...)` in half a dozen places (morning
    # init, the smart planner, /api/daily/tasks, get_today_state). Without
    # this column every one of those calls raises immediately. Restored it.
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # FIX (multi-user): was `unique=True` globally, which meant only ONE user
    # in the entire system could ever have a "2026-08-06" row. Uniqueness is
    # now per-user via the UniqueConstraint below.
    date = Column(String(10), nullable=False)
    mood = Column(String(100), nullable=True)
    energy = Column(String(100), nullable=True)
    stress_level = Column(String(100), nullable=True)
    focus_level = Column(String(100), nullable=True)
    sleep_hours = Column(Float, nullable=True)
    sleep_quality = Column(String(50), nullable=True)
    current_tasks = _json_col(nullable=True, default=list)
    blockers = _json_col(nullable=True, default=list)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_daily_state_user_date"),)


class EventTask(Base):
    __tablename__ = "events_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)  # win, setback, milestone, task
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    impact_level = Column(Integer, default=5)
    emotion = Column(String(100), nullable=True)
    lesson_learned = Column(Text, nullable=True)
    related_goal_id = Column(
        Integer, ForeignKey("goals.id", ondelete="SET NULL"), nullable=True
    )
    tags = _json_col(nullable=True, default=list)
    occurred_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    habit_type = Column(String(50), default="positive")
    frequency = Column(String(50), default="daily")
    target_count = Column(Integer, default=1)
    category = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    streak_current = Column(Integer, default=0)
    streak_best = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HabitLog(Base):
    __tablename__ = "habit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Denormalized alongside habit_id (rather than joining through Habit) so
    # habit-log queries can be scoped to a user without an extra join.
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    habit_id = Column(
        Integer, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False
    )
    date = Column(String(10), nullable=False)
    completed = Column(Boolean, default=True)
    count = Column(Integer, default=1)
    quality = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    logged_at = Column(DateTime, default=datetime.utcnow)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(
        BigInteger if _IS_POSTGRES else Integer,
        primary_key=True,
        autoincrement=True,
    )
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(100), index=True, nullable=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ContextSnapshot(Base):
    __tablename__ = "context_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(100), index=True, nullable=False)
    summary = Column(Text, nullable=False)
    active_tasks = _json_col(nullable=True, default=list)
    key_decisions = _json_col(nullable=True, default=list)
    open_questions = _json_col(nullable=True, default=list)
    mood_at_end = Column(String(100), nullable=True)
    topics_discussed = _json_col(nullable=True, default=list)
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class WeeklySchedule(Base):
    """
    LEGACY (پیش از معماری TaskSlot): یک بلاب JSON در سطح هر هفته که همه‌ی
    اسلات‌های آن هفته (کلید «YYYY-MM-DD|HH») را در یک ستون نگه می‌داشت.

    این جدول دیگر برای نوشتن استفاده نمی‌شود — منبع حقیقتِ تسک‌های
    تاریخ‌دار حالا `TaskSlot` (پایین همین فایل) است: هر تسک یک ردیف مجزا،
    نه یک کلید داخل یک بلاب مشترک. دلیل تغییر:
      1) هر نوشتن روی یک اسلات، کل بلاب هفته را read-modify-write می‌کرد؛
         دو درخواست هم‌زمان (مثلاً چت + کلیک تیک در صفحه‌ی Daily) می‌تونستن
         تغییر همدیگه رو با یه lost update پاک کنن.
      2) داده به‌صورت متن/JSONB بود، نه ردیف‌های ایندکس‌شده — کوئری زدن
         («همه‌ی تسک‌های سررسیدگذشته») عملاً غیرممکن بود.
    جدول و مدل اینجا فقط برای backward-compat و migration نگه داشته شده
    (`_migrate_weekly_schedule_to_task_slots` در `init_db()` محتوای قدیمی
    را یک‌بار به TaskSlot منتقل می‌کند) — کد جدید نباید مستقیم بهش بنویسه.
    """
    __tablename__ = "weekly_schedule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # FIX (multi-user): was `unique=True` globally (same bug class as
    # DailyState.date) — every user would collide on the same ISO week.
    week_key = Column(String(20), index=True, nullable=False)
    schedule_data = _json_col(nullable=True, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "week_key", name="uq_weekly_schedule_user_week"),)


class TaskSlot(Base):
    """
    منبع حقیقتِ واحد برای همه‌ی تسک‌های تاریخ‌دار (چه از صفحه‌ی Daily/Weekly
    ثبت شده باشن، چه از طریق چت/smart planner). جایگزین WeeklySchedule
    (بالا) به‌عنوان مدل ذخیره‌سازی — همون مفهوم «یک اسلات = یک تاریخ + یک
    ساعت»، ولی هر اسلات حالا یک ردیف مستقل و ایندکس‌شده‌ست، نه یک کلید
    داخل یک بلاب JSON مشترک با بقیه‌ی اسلات‌های همون هفته.

    مزیت‌ها نسبت به بلاب:
      - نوشتن روی یک اسلات فقط همون ردیف رو لاک می‌کنه (نه کل هفته رو) —
        UniqueConstraint زیر تضمین می‌کنه دو نوشتن هم‌زمان روی یک اسلات
        با خطای DB مواجه بشن، نه با پاک‌شدن خاموشِ یکی‌شون.
      - Daily view و Weekly view و AI (memory_manager.get_context_for_llm)
        الان همه از همین یک جدول می‌خونن — دیگه امکان نداره صفحه‌ی Daily
        یه چیز نشون بده و حافظه‌ی مکالمه چیز دیگه‌ای فکر کنه.
      - قابل کوئری با فیلتر/ایندکس معمولی SQL (بازه‌ی تاریخ، completed=False و...).
    """
    __tablename__ = "task_slots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD (تقویم ایران)
    hour = Column(Integer, nullable=False)  # 0-23
    text = Column(Text, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "date", "hour", name="uq_task_slot_user_date_hour"),
    )


# -----------------------------------------------------------------------------
# New Models: WorkTask, Reminder, PomodoroSession
# -----------------------------------------------------------------------------
class WorkTask(Base):
    __tablename__ = "work_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)

    scheduled_date = Column(String(10), nullable=True)  # YYYY-MM-DD
    scheduled_day = Column(String(30), nullable=True)  # e.g. Monday
    scheduled_hour = Column(String(20), nullable=True)  # e.g. 14:30

    # FIX: renamed from due_at to match scheduler/main usage; kept as nullable
    due_at = Column(DateTime, nullable=True)

    estimated_pomodoros = Column(Integer, default=1)
    completed_pomodoros = Column(Integer, default=0)
    current_progress = Column(Float, default=0.0)

    difficulty = Column(Integer, default=1)  # FIX: int to match Pydantic model
    cognitive_load = Column(Float, default=0.0)  # FIX: float to match Pydantic model
    cognitive_intensity = Column(Float, default=0.0)  # FIX: float
    mental_fatigue = Column(
        Float, default=0.0
    )  # FIX: renamed from mental_fatigue_estimate, float
    focus_requirements = Column(
        String(50), nullable=True
    )  # FIX: renamed from focus_requirement

    status = Column(
        String(50), default="pending"
    )  # pending, in_progress, completed, blocked
    is_blocked = Column(Boolean, default=False)

    # FIX: renamed from 'metadata' (reserved word in SQLAlchemy declarative API)
    extra_metadata = _json_col(nullable=True, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def apply_pomodoro_completion(task: "WorkTask") -> None:
    """Shared logic for crediting a completed *focus* pomodoro to its task.

    Used by both the manual `/api/pomodoro/stop` endpoint (main.py) and the
    background scheduler's auto-complete path (scheduler_service.py) so that
    manual and automatic completion behave identically.
    """
    task.completed_pomodoros = (task.completed_pomodoros or 0) + 1
    if task.estimated_pomodoros and task.estimated_pomodoros > 0:
        task.current_progress = min(
            100.0,
            (task.completed_pomodoros / task.estimated_pomodoros) * 100,
        )
    task.mental_fatigue = min(
        10.0, (task.mental_fatigue or 0.0) + (task.difficulty or 0) * 0.1
    )


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)

    reminder_type = Column(String(50), nullable=False, default="general")
    related_task_id = Column(
        Integer, ForeignKey("work_tasks.id", ondelete="SET NULL"), nullable=True
    )
    related_weekly_slot = Column(String(100), nullable=True)

    # FIX: renamed from remind_at to reminder_at to match main.py / Pydantic models
    # FIX (Supabase/serverless migration): now timezone-aware (TIMESTAMPTZ on
    # Postgres) so scheduling comparisons against datetime.now(timezone.utc)
    # in the /api/cron/check-reminders endpoint (main.py) and
    # scheduler_service.py are unambiguous regardless of the DB session's
    # timezone setting.
    reminder_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # NOTE: this boolean *is* the "is_notified" flag used by the cron/
    # notification pipeline — kept named `sent` (rather than renamed) so we
    # don't have to touch every existing call site (reminder CRUD endpoints,
    # the background scheduler, and reminder_to_dict()) that already depends
    # on this exact field name.
    sent = Column(Boolean, default=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    priority = Column(Integer, default=1)
    language = Column(String(10), default="fa")
    rtl = Column(Boolean, default=True)
    avatar_emotion = Column(String(50), nullable=True)

    # FIX: renamed from 'metadata' (reserved word in SQLAlchemy declarative API)
    extra_metadata = _json_col(nullable=True, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PomodoroSession(Base):
    __tablename__ = "pomodoro_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(
        Integer, ForeignKey("work_tasks.id", ondelete="SET NULL"), nullable=True
    )

    session_type = Column(String(20), nullable=False, default="focus")  # focus / break
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)  # FIX: nullable — set on stop
    actual_end_time = Column(DateTime, nullable=True)

    duration_minutes = Column(Integer, nullable=False, default=25)
    status = Column(
        String(50), nullable=False, default="pending"
    )  # pending, active, completed, cancelled, paused

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PendingPlan(Base):
    """
    پیشنهادهای «تجزیه‌ی شناختی» که smart planner توی چت مطرح می‌کنه و منتظر
    تأیید کاربر می‌مونه (نه قفل خودکار). وقتی کاربر توی پیام بعدی تأیید کرد،
    بلوک‌ها قفل می‌شن و status=applied می‌شه؛ رد بشه discarded. جدول جدیده
    پس create_all روی استارتاپ خودش می‌سازدش (نیازی به migration نیست).
    """
    __tablename__ = "pending_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_json = Column(Text, nullable=False)  # JSON: [{"date","hour","text"}, ...]
    status = Column(String(20), default="proposed", index=True)  # proposed / applied / discarded
    created_at = Column(DateTime, default=datetime.utcnow)


# -----------------------------------------------------------------------------
# DB Init Helpers
# -----------------------------------------------------------------------------
def _column_exists(conn, table: str, column: str) -> bool:
    """بررسی وجود ستون برای دیتابیس‌هایی که IF NOT EXISTS ندارند (SQLite)."""
    from sqlalchemy import text as _text

    if _IS_POSTGRES:
        row = conn.execute(
            _text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_name = :t AND column_name = :c"
            ),
            {"t": table, "c": column},
        ).first()
        return row is not None
    # SQLite
    rows = conn.execute(_text(f"PRAGMA table_info({table})")).fetchall()
    return any(r[1] == column for r in rows)


def _migrate_weekly_schedule_to_task_slots() -> None:
    """
    یک‌باره (و idempotent) هر بلاب JSON قدیمی در WeeklySchedule.schedule_data
    را به ردیف‌های TaskSlot تبدیل می‌کند — تا با معماری جدید (TaskSlot به‌جای
    بلاب هفتگی، رجوع کنید به کامنت بالای هر دو کلاس)، تسک‌های قدیمی کاربرها
    گم نشن.

    Idempotent از دو طریق:
      1) اگر TaskSlot از قبل برای آن (user_id, date, hour) ردیفی دارد،
         دست‌نخورده رد می‌شود (یعنی اجرای دوباره‌ی این تابع هیچ آسیبی نمی‌زند).
      2) کل عملیات داخل except عمومی است — یک بلاب خراب کل migration را
         متوقف نمی‌کند، فقط همان یک رکورد لاگ و رد می‌شود.

    عمداً WeeklySchedule را پاک/خالی نمی‌کند (فقط از آن می‌خواند) — اگر یک‌بار
    این تابع ناقص اجرا شود، دفعه‌ی بعدِ استارتاپ باز هم می‌تواند از همان بلاب
    قدیمی بخواند و باقی‌مانده را کامل کند.
    """
    from sqlalchemy import text as _text

    with engine.begin() as conn:
        # جدول TaskSlot باید از قبل (توسط create_all بالاتر) ساخته شده باشد.
        rows = conn.execute(_text("SELECT user_id, week_key, schedule_data FROM weekly_schedule")).fetchall()
        if not rows:
            return

        migrated = 0
        for user_id, week_key, schedule_data in rows:
            try:
                data = json.loads(schedule_data) if isinstance(schedule_data, str) else schedule_data
                if not isinstance(data, dict):
                    continue
                for key, val in data.items():
                    try:
                        date_part, hour_part = str(key).rsplit("|", 1)
                        hour = int(hour_part)
                    except ValueError:
                        continue  # کلید فرمت قدیمی‌تر («شنبه-10») — قبلاً هم main.py این‌ها رو تبدیل می‌کرد؛ اینجا از قلم می‌افتن ولی چیزی خراب نمی‌شه
                    if isinstance(val, dict):
                        text_val, completed_val = str(val.get("text", "")), bool(val.get("completed"))
                    else:
                        text_val, completed_val = str(val), False
                    if not text_val:
                        continue

                    exists = conn.execute(
                        _text(
                            "SELECT 1 FROM task_slots WHERE user_id=:u AND date=:d AND hour=:h"
                        ),
                        {"u": user_id, "d": date_part, "h": hour},
                    ).first()
                    if exists:
                        continue

                    conn.execute(
                        _text(
                            "INSERT INTO task_slots (user_id, date, hour, text, completed, created_at, updated_at) "
                            "VALUES (:u, :d, :h, :t, :c, :now, :now)"
                        ),
                        {
                            "u": user_id, "d": date_part, "h": hour, "t": text_val,
                            "c": completed_val, "now": datetime.utcnow(),
                        },
                    )
                    migrated += 1
            except Exception as e:
                print(f"⚠️ migration notice: skipped one weekly_schedule row (user_id={user_id}, week_key={week_key}): {e}")

        if migrated:
            print(f"✅ Migrated {migrated} legacy schedule slot(s) from weekly_schedule into task_slots.")


def init_db():
    """
    ساخت جداول + auto-migration ستون‌های توکن ریست/تأیید ایمیل روی جدول users.
    create_all() فقط جدول‌های *جدید* را می‌سازد و ستون‌های اضافه‌شده به مدل‌های
    موجود را به دیتابیس قبلی اضافه نمی‌کند — اینجا با ALTER TABLE خام جبران
    می‌شود تا دیتابیس لایو همیشه بدون migration دستی به‌روز باشد.
    """
    Base.metadata.create_all(bind=engine)

    try:
        _migrate_weekly_schedule_to_task_slots()
    except Exception as e:
        print(f"⚠️ weekly_schedule → task_slots migration skipped: {e}")
    try:
        if _IS_POSTGRES:
            # PostgreSQL از ADD COLUMN IF NOT EXISTS پشتیبانی می‌کند — idempotent
            with engine.begin() as conn:
                conn.exec_driver_sql(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_password_token VARCHAR(255);"
                )
                conn.exec_driver_sql(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_password_expires_at TIMESTAMP;"
                )
                conn.exec_driver_sql(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token_hash VARCHAR(255);"
                )
                conn.exec_driver_sql(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token_expires TIMESTAMP;"
                )
                conn.exec_driver_sql(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;"
                )
            print("✅ Users table auto-migrated successfully.")
        else:
            # SQLite از IF NOT EXISTS در ADD COLUMN پشتیبانی نمی‌کند؛ همان منطق
            # با چک PRAGMA اجرا می‌شود.
            new_columns = {
                "reset_password_token": "VARCHAR(255)",
                "reset_password_expires_at": "TIMESTAMP",
                "verification_token_hash": "VARCHAR(255)",
                "verification_token_expires": "TIMESTAMP",
                "email_verified": "BOOLEAN DEFAULT 0 NOT NULL",
            }
            from sqlalchemy import text as _text

            with engine.connect() as conn:
                added = False
                for col, col_type in new_columns.items():
                    if not _column_exists(conn, "users", col):
                        conn.execute(_text(f"ALTER TABLE users ADD COLUMN {col} {col_type}"))
                        added = True
                conn.commit()
            if added:
                print("✅ Users table auto-migrated successfully (SQLite).")
    except Exception as e:
        print(f"⚠️ Auto-migration notice: {e}")
