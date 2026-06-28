import os
from contextlib import contextmanager
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    Boolean,
    BigInteger,
    JSON,
)
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import event


# -----------------------------------------------------------------------------
# Database URL / Engine
# -----------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./jarvis.db")

# Normalize legacy postgres URL scheme if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

_IS_SQLITE = DATABASE_URL.startswith("sqlite")
_IS_POSTGRES = DATABASE_URL.startswith("postgresql") or DATABASE_URL.startswith("postgres")

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

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
# Existing Models
# -----------------------------------------------------------------------------
class Persona(Base):
    __tablename__ = "persona"

    id = Column(Integer, primary_key=True, default=1)
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

    id = Column(Integer, primary_key=True, default=1)
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


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
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

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), unique=True, nullable=False)
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


class EventTask(Base):
    __tablename__ = "events_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(100), nullable=False)  # win, setback, milestone, task
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    impact_level = Column(Integer, default=5)
    emotion = Column(String(100), nullable=True)
    lesson_learned = Column(Text, nullable=True)
    related_goal_id = Column(Integer, nullable=True)  # soft link to goals
    tags = _json_col(nullable=True, default=list)
    occurred_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, autoincrement=True)
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
    habit_id = Column(Integer, nullable=False)  # soft FK to habits
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
    session_id = Column(String(100), index=True, nullable=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ContextSnapshot(Base):
    __tablename__ = "context_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
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
    __tablename__ = "weekly_schedule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    week_key = Column(String(20), unique=True, index=True, nullable=False)
    schedule_data = _json_col(nullable=True, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# -----------------------------------------------------------------------------
# New Models: WorkTask, Reminder, PomodoroSession
# -----------------------------------------------------------------------------
class WorkTask(Base):
    __tablename__ = "work_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)

    scheduled_date = Column(String(10), nullable=True)    # YYYY-MM-DD
    scheduled_day = Column(String(30), nullable=True)     # e.g. Monday
    scheduled_hour = Column(String(20), nullable=True)    # e.g. 14:30

    # FIX: renamed from due_at to match scheduler/main usage; kept as nullable
    due_at = Column(DateTime, nullable=True)

    estimated_pomodoros = Column(Integer, default=1)
    completed_pomodoros = Column(Integer, default=0)
    current_progress = Column(Float, default=0.0)

    difficulty = Column(Integer, default=1)               # FIX: int to match Pydantic model
    cognitive_load = Column(Float, default=0.0)           # FIX: float to match Pydantic model
    cognitive_intensity = Column(Float, default=0.0)      # FIX: float
    mental_fatigue = Column(Float, default=0.0)           # FIX: renamed from mental_fatigue_estimate, float
    focus_requirements = Column(String(50), nullable=True) # FIX: renamed from focus_requirement

    status = Column(String(50), default="pending")        # pending, in_progress, completed, blocked
    is_blocked = Column(Boolean, default=False)

    # FIX: renamed from 'metadata' (reserved word in SQLAlchemy declarative API)
    extra_metadata = _json_col(nullable=True, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)

    reminder_type = Column(String(50), nullable=False, default="general")
    related_task_id = Column(Integer, nullable=True)        # soft link to WorkTask
    related_weekly_slot = Column(String(100), nullable=True)

    # FIX: renamed from remind_at to reminder_at to match main.py / Pydantic models
    reminder_at = Column(DateTime, nullable=False, index=True)

    # FIX: renamed from is_sent to sent to match main.py usage
    sent = Column(Boolean, default=False, index=True)
    sent_at = Column(DateTime, nullable=True)

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
    task_id = Column(Integer, nullable=True)  # soft link to WorkTask

    session_type = Column(String(20), nullable=False, default="focus")  # focus / break
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)          # FIX: nullable — set on stop
    actual_end_time = Column(DateTime, nullable=True)

    duration_minutes = Column(Integer, nullable=False, default=25)
    status = Column(String(50), nullable=False, default="pending")  # pending, active, completed, cancelled, paused

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# -----------------------------------------------------------------------------
# DB Init Helpers
# -----------------------------------------------------------------------------
def init_db():
    Base.metadata.create_all(bind=engine)
