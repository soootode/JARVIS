"""
main.py - Jarvis-You Backend
Milestone 2: SQLAlchemy + Context Snapshots + Session Management
+ DailyView / WeeklyView endpoints
+ Morning Initialization Protocol
<<<<<<< HEAD
+ Google Gemini (via the OpenAI-compatible endpoint)
"""

# ── Imports ───────────────────────────────────────────────────────
import asyncio
import json
import logging
import os
import uuid
from datetime import date as date_type, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# FIX (Vercel): python-dotenv is a dev-convenience dependency for loading a
# local .env file. Vercel (and most serverless/production hosts) injects
# real environment variables directly and doesn't need it, so it may not be
# installed there. Fall back to a no-op `load_dotenv()` instead of crashing
# the whole app with an ImportError if the package is absent.
try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args, **kwargs):
        return False

# FIX: load_dotenv() must run BEFORE `database` (and `auth`) are imported,
# since both read env vars (DATABASE_URL, JWT_SECRET_KEY) at *module import
# time*, not inside a function. With the old import order, a local .env file
# was silently ignored and the app always fell back to sqlite:///./jarvis.db
# regardless of what DATABASE_URL said — it only ever worked in production
# because platforms like Liara inject real environment variables directly
# (not via a .env file), which masked the bug.
load_dotenv()

from fastapi import Depends, FastAPI, Header, HTTPException
=======
+ GapGPT (OpenAI-compatible)
"""

# ── Imports ────────────────────────────────────────────────────────────────────
import asyncio
import json
import os
import uuid
from datetime import date as date_type, datetime, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler

<<<<<<< HEAD
from auth import router as auth_router, get_current_user
from memory_manager import MemoryManager
from memory_updater import extract_memory_updates
from push_service import dispatch_reminder_notifications
from scheduler_service import SchedulerService
from sqlalchemy.exc import IntegrityError

from database import (
    get_session, init_db,
    User, DailyState, EventTask, Habit, Goal, TaskSlot,
    WorkTask, Reminder, PomodoroSession, Psychology, PendingPlan,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jarvis.main")
=======
from memory_manager import MemoryManager
from memory_updater import extract_memory_updates
from scheduler_service import SchedulerService
from database import (
    get_session, init_db,
    DailyState, EventTask, Habit, Goal, WeeklySchedule,
    WorkTask, Reminder, PomodoroSession,
)

load_dotenv()
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9

scheduler = None
scheduler_service = None

<<<<<<< HEAD
# ── Startup validation ─────────────────────────────────────────

# این سرویس از طریق همان endpoint سازگار با OpenAI که Google Gemini رسمی ارائه
# می‌ده وصل می‌شه (https://generativelanguage.googleapis.com/v1beta/openai/) — یعنی
# کد فراخوانی client.chat.completions.create() در همه جا بدون تغییر می‌مونه.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError(
        "❌ GOOGLE_API_KEY در .env پیدا نشد.\n"
        "از Google AI Studio (https://aistudio.google.com/apikey) یک کلید API بساز.\n"
        "سپس در .env بنویس: GOOGLE_API_KEY=your_key_here"
    )

client = OpenAI(
    api_key=GOOGLE_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# FIX: هاردکد بودن اسم مدل باعث می‌شه وقتی مدل deprecated بشه، سرور با 404 از
# کار بیافتد. الان از .env می‌خونه، پیش‌فرضش یک مدل Gemini رایج و پایداره.
# اگر Google باز مدل رو عوض کرد، فقط همین یه خط env نیاز به تفییر داره.
MODEL = os.getenv("LLM_MODEL", "gemini-3.6-flash")

# ── Cron security (Vercel Cron -> GET /api/cron/check-reminders) ─────────────
CRON_SECRET = os.getenv("CRON_SECRET")
=======
# ── Startup validation ─────────────────────────────────────────────────────────

GAPGPT_API_KEY = os.getenv("GAPGPT_API_KEY")
if not GAPGPT_API_KEY:
    raise RuntimeError(
        "❌ GAPGPT_API_KEY در .env پیدا نشد.\n"
        "از پنل گپ‌جی‌پی‌تی کلید API بساز.\n"
        "سپس در .env بنویس: GAPGPT_API_KEY=your_key_here"
    )

client = OpenAI(
    api_key=GAPGPT_API_KEY,
    base_url="https://api.gapgpt.app/v1",
)

MODEL = "gpt-5.3-chat-latest"
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9

# ── App setup ──────────────────────────────────────────────────────────────────

app = FastAPI(title="Jarvis-You Backend")
<<<<<<< HEAD

# FIX (multi-user): frontend origin now comes from env instead of only
# hardcoded localhost, so a deployed frontend can actually call this API.
# FIX (Failed to fetch on auth pages): فرانت دیپلوی‌شده (ورکشنری/پرویوهای
# ورکسل) دامنه‌های متغیری دارد که با allowlist ثابت جا می‌ماندند و CORS
# درخواست‌های auth را می‌بُرد. پیش‌فرض حالا wildcard است؛ برای محدودسازی،
# متغیر env به نام CORS_ORIGINS را با لیست کاما-جدا ست کنید.
_extra_origin = os.getenv("FRONTEND_ORIGIN")
_cors_origins_env = os.getenv("CORS_ORIGINS")
if _cors_origins_env:
    _cors_origins = [o.strip() for o in _cors_origins_env.split(",") if o.strip()]
elif _extra_origin:
    _cors_origins = ["http://localhost:5173", "http://localhost:3000", _extra_origin]
else:
    _cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
=======
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        # بعد از دیپلوی لیارا، آدرس فرانت‌اند را اینجا اضافه کن:
        # "https://jarvis-frontend.liara.run",
        # "https://yourdomain.ir",
    ],
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< HEAD
app.include_router(auth_router)

# FIX (multi-user): MemoryManager used to be a single global instance shared
# by every request (SESSION_ID was one UUID for the whole process — there
# was no concept of "which user" at all). It is now instantiated per-request
# inside each endpoint as `MemoryManager(user_id=current_user.id)`, using a
# per-process chat-session id only for grouping a browser session's messages.
PROCESS_SESSION_ID = str(uuid.uuid4())


class LLMUnavailableError(Exception):
    """Raised by _call_llm when Gemini can't be reached (rate-limited,
    quota exhausted, or any other API failure). Carries a Persian message
    that's safe to show directly to the user, so callers can turn it into
    a proper HTTP status instead of a bare 500."""
    pass


# FIX (bug #4 — تاریخ اشتباه نزدیک نیمه‌شب): Vercel روی UTC اجرا می‌شه.
# date_type.today() ساعت سرور رو می‌گیره، نه ساعت ایران — یعنی از ساعت
# ۰۳:۳۰ بامداد تا نیمه‌شب به وقت ایران (که معادل ۰۰:۰۰ تا ۲۰:۳۰ UTC است)
# مشکلی نیست، اما بین ساعت ۲۰:۳۰ تا نیمه‌شب UTC (یعنی ۰۰:۰۰ تا ۰۳:۳۰ بامداد
# به وقت ایران) `date_type.today()` هنوز روز قبل رو برمی‌گردونه در حالی که
# برای کاربر همون روز جدید شروع شده. عکسش هم صادقه: کاربری که ساعت ۲۳:۳۰
# شب (وقت ایران) چت می‌کنه در واقع ساعت ۲۰:۰۰ UTC است که هنوز "امروز"ه —
# پس اون مورد خاص در مثال باگ گزارش‌شده اشتباه بود، ولی اصل مشکل (عدم
# تطابق منطقه‌ی زمانی) واقعیه و در بازه‌ی نزدیک نیمه‌شب سرچشمه‌ی خطاست.
# ایران از سال ۱۴۰۱ (۲۰۲۲) DST را کنار گذاشته، پس آفست همیشه ثابت +۳:۳۰ است.
IRAN_UTC_OFFSET = timedelta(hours=3, minutes=30)


def _now_iran() -> datetime:
    return datetime.now(timezone.utc) + IRAN_UTC_OFFSET


def _today_iran() -> date_type:
    return _now_iran().date()

# ── Startup: ساخت جداول دیتابیس ────────────────────────────────────────────

# FIX (serverless resilience): auto-creating tables on every cold start is
# convenient for a small app with no separate migrations tool, but it means
# a transient DB connection hiccup (e.g. Supabase waking up from a pause, a
# brief network blip) previously raised straight out of the FastAPI startup
# event and crashed the *entire* app before it could serve even a trivial
# request like GET /. Two independent safeguards now guard against that:
#   1. SKIP_DB_INIT=1 lets ops disable the automatic init_db() call entirely
#      (e.g. once schema changes are managed by a separate migrations tool).
#   2. Even when enabled, a failure is caught and logged as a warning
#      instead of propagating, so the app still boots and can serve
#      requests that don't need a freshly created table.
_SKIP_DB_INIT = os.getenv("SKIP_DB_INIT", "").strip().lower() in ("1", "true", "yes")

=======
SESSION_ID = str(uuid.uuid4())
memory_manager = MemoryManager(session_id=SESSION_ID)

# ── Startup: ساخت جداول دیتابیس ───────────────────────────────────────────────
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9

@app.on_event("startup")
async def startup():
    global scheduler, scheduler_service

<<<<<<< HEAD
    if _SKIP_DB_INIT:
        print("⏭️  SKIP_DB_INIT is set — skipping init_db() (assuming schema is already migrated)")
    else:
        try:
            init_db()
            print("✅ Database tables ready")
        except Exception as e:
            logger.warning(f"⚠️ init_db() failed at startup, continuing without it: {e}")

    # FIX (serverless): APScheduler's BackgroundScheduler needs a long-lived
    # process with a persistent thread. On Vercel, each invocation may run in
    # a brand-new, short-lived instance — a background thread started here
    # has no guarantee of ever ticking again after the current request
    # finishes, so keeping it enabled just wastes cold-start time and can
    # leak threads across warm invocations. `VERCEL` is set automatically by
    # the Vercel runtime. Scheduled reminder checks are instead driven by
    # Vercel Cron hitting GET /api/cron/check-reminders (see vercel.json).
    # The in-process scheduler is kept for traditional long-running
    # deployments (Liara, Docker, bare uvicorn, etc.).
    if os.getenv("VERCEL"):
        print("⏭️  Running on Vercel — skipping in-process scheduler (using Vercel Cron instead)")
        return
=======
    init_db()
    print("✅ Database tables ready")
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9

    try:
        scheduler_service = SchedulerService()
        scheduler = BackgroundScheduler()

        scheduler.add_job(
            scheduler_service.run_all,
            "interval",
            seconds=60,
            id="task_reminder_job",
            replace_existing=True,
        )

        scheduler.start()
        print("⏰ Background Scheduler started: Checking reminders every 60s")
    except Exception as e:
        print(f"❌ Failed to start scheduler: {e}")


@app.on_event("shutdown")
async def shutdown():
    global scheduler
    if scheduler:
        scheduler.shutdown(wait=False)
        print("🛑 Background Scheduler stopped")


# ── Load config files ──────────────────────────────────────────────────────────

def load_text(path: str, fallback: str = "") -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8") if p.exists() else fallback


def load_json(path: str) -> dict:
    p = Path(path)
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


SYSTEM_PROMPT_BASE = load_text("system_prompt.txt", "شما یک دستیار هوشمند هستید.")
<<<<<<< HEAD

# FIX (multi-user): persona.json used to be injected verbatim into every
# request's system prompt via a global PERSONA_JSON — but persona.json is
# ONE person's real psychological profile (trauma points, attachment style,
# etc.). Broadcasting it to every signed-up user would be a serious data
# leak, not a bug fix. It is intentionally no longer auto-loaded here.
# Per-user personalization now comes only from `memory_manager.get_persona()`
# / `get_psychology()` — i.e. whatever that specific user entered during
# onboarding — via get_context_for_llm() below.
#
# If you want persona.json's *content* preserved for your own account, run
# it through the onboarding flow (or a one-off seed script scoped to your
# own user_id) instead of loading the file globally.


def build_system_prompt(memory_manager: MemoryManager) -> str:
    prompt = SYSTEM_PROMPT_BASE

    # FIX: مدل قبلاً هیچ اطلاع مستقیمی از تاریخ/روز واقعی نداشت و مجبور بود
    # از روی تاریخچه‌ی چت حدس بزنه امروز چه روزیه — که توی روزهای پشت‌سرهم
    # (مثلاً پنجشنبه، وقتی آخرین اشاره‌ی صریح به روز توی چت مال چهارشنبه
    # بود) به‌راحتی اشتباه می‌رفت. الان تاریخ/روز واقعی (به وقت ایران) صریح
    # به اول سیستم‌پرامپت تزریق می‌شه.
    today_fa = _get_persian_day(_today_iran())
    today_str = _today_str()
    prompt += (
        f"\n\n---\nاطلاعات زمانی زنده سیستم:\n"
        f"امروز واقعاً «{today_fa}» (تاریخ: {today_str}) است. تمام برنامه‌ریزی‌ها "
        f"و پاسخ‌ها باید بر همین مبنا باشه، نه حدس از روی چت‌های قبلی.\n"
    )

=======
PERSONA_JSON = load_json("persona.json")


def build_system_prompt() -> str:
    prompt = SYSTEM_PROMPT_BASE
    if PERSONA_JSON:
        prompt += (
            "\n\n---\nPROFILE DATA (اطلاعات شخصی کاربر - JSON):\n"
            + json.dumps(PERSONA_JSON, ensure_ascii=False, indent=2)
        )
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    memory_context = memory_manager.get_context_for_llm()
    if memory_context and memory_context != "حافظه‌ای ثبت نشده است.":
        prompt += f"\n\n---\nVARIABLE MEMORY (وضعیت فعلی کاربر):\n{memory_context}"
    return prompt


# ── Pydantic models ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    session_id: str


class DailyStateUpdate(BaseModel):
    mood: str = None
    energy: str = None
    stress_level: str = None
    focus_level: str = None
    sleep_hours: float = None
    sleep_quality: str = None
    current_tasks: list[str] = None
    blockers: list[str] = None
    notes: str = None


class SessionCloseRequest(BaseModel):
    summary: str
    active_tasks: list[str] = []
    key_decisions: list[str] = []
    open_questions: list[str] = []
    mood_at_end: str = None
    topics_discussed: list[str] = []


class NewTaskRequest(BaseModel):
    text: str


class WorkTaskCreateRequest(BaseModel):
    title: str
    description: str | None = None
    due_at: str | None = None
    estimated_pomodoros: int = 1
    difficulty: int = 1
    cognitive_load: float = 0.0
    cognitive_intensity: float = 0.0
    mental_fatigue: float = 0.0
    focus_requirements: str | None = None
    extra_metadata: dict | None = None  # FIX: renamed from metadata


class WorkTaskUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    due_at: str | None = None
    estimated_pomodoros: int | None = None
    completed_pomodoros: int | None = None
    current_progress: float | None = None
    difficulty: int | None = None
    cognitive_load: float | None = None
    cognitive_intensity: float | None = None
    mental_fatigue: float | None = None
    focus_requirements: str | None = None
    status: str | None = None
    extra_metadata: dict | None = None  # FIX: renamed from metadata


class ReminderCreateRequest(BaseModel):
    title: str
    message: str
    reminder_at: str
    reminder_type: str = "general"
    priority: int = 1
    language: str = "fa"
    rtl: bool = True
    avatar_emotion: str | None = None
    extra_metadata: dict | None = None  # FIX: renamed from metadata


class ReminderUpdateRequest(BaseModel):
    title: str | None = None
    message: str | None = None
    reminder_at: str | None = None
    reminder_type: str | None = None
    priority: int | None = None
    sent: bool | None = None
    language: str | None = None
    rtl: bool | None = None
    avatar_emotion: str | None = None
    extra_metadata: dict | None = None  # FIX: renamed from metadata


class TaskToggleRequest(BaseModel):
    task_text: str
    completed: bool


class FeedbackRequest(BaseModel):
    feedback: str


class WeeklyScheduleRequest(BaseModel):
    schedule: dict


<<<<<<< HEAD
class OnboardingRequest(BaseModel):
    preferred_name: str
    age: int | None = None
    occupation: str | None = None
    education_level: str | None = None
    life_philosophy: str | None = None
    core_values: list[str] = []
    learning_style: str | None = None          # → communication_style
    main_challenges: list[str] = []            # → stress_triggers
    motivators: list[str] = []                 # → motivators


=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
class PomodoroStartRequest(BaseModel):
    task_id: int | None = None
    duration_minutes: int = 25
    session_type: str = "focus"  # focus, short_break, long_break


class PomodoroStopRequest(BaseModel):
    completed: bool = True


# ── Helper: parse datetime string ─────────────────────────────────────────────

def _parse_dt(dt_str: str | None):
<<<<<<< HEAD
    """
    Parses an ISO-8601 datetime string into a timezone-aware `datetime`.
    FIX (Supabase/serverless migration): Reminder.reminder_at is now a
    TIMESTAMPTZ column. Browsers send ISO strings ending in "Z" (e.g. from
    `Date.prototype.toISOString()`), which `datetime.fromisoformat()` cannot
    parse on Python < 3.11 and which produces a *naive* datetime even when it
    can. Normalize "Z" -> "+00:00", and if the result is still naive, assume
    it's UTC so every reminder-related datetime in the app is comparable.
    """
    if not dt_str:
        return None
    try:
        normalized = dt_str[:-1] + "+00:00" if dt_str.endswith("Z") else dt_str
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
=======
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    except Exception:
        return None


# ── Helpers ────────────────────────────────────────────────────────────────────

def build_chat_history(history: list[dict]) -> list[dict]:
    result = []
    for msg in history:
        role = "assistant" if msg["role"] == "assistant" else "user"
        result.append({"role": role, "content": msg["content"]})
    return result


def _call_llm(
    system_prompt: str,
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 1500,
) -> str:
<<<<<<< HEAD
    # FIX (bug #2 — 500 on Gemini rate limit): this had zero error handling,
    # so a 429 from Gemini (quota exhausted — easy to hit on the free tier
    # under real chat volume) surfaced as an unhandled exception, which
    # every call site's `except Exception` turned into a generic 500 with
    # no useful message. Now we catch it here and raise a dedicated
    # LLMUnavailableError with a friendly Persian message, so /api/chat
    # (and every other caller) can return a proper 429/503 instead of a 500.
    all_messages = [{"role": "system", "content": system_prompt}] + messages
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=all_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        msg = str(e)
        is_rate_limit = (
            "429" in msg
            or "rate limit" in msg.lower()
            or "quota" in msg.lower()
            or getattr(e, "status_code", None) == 429
        )
        if is_rate_limit:
            print(f"⚠️ LLM rate limited: {e}")
            raise LLMUnavailableError(
                "سهمیه‌ی درخواست‌های لحظه‌ای پر شده. لطفاً چند ثانیه دیگر دوباره پیام بده."
            ) from e
        print(f"⚠️ LLM call failed: {e}")
        raise LLMUnavailableError(
            "در حال حاضر امکان پاسخ‌گویی نیست. لطفاً کمی بعد دوباره تلاش کن."
        ) from e


def _today_str() -> str:
    return _today_iran().isoformat()


def _current_week_key() -> str:
    today = _today_iran()
    return f"{today.year}-W{today.isocalendar()[1]:02d}"


def _week_key_for_offset(week_offset: int) -> str:
    """FIX (4-week navigation): given an integer offset in weeks from the
    current week (0 = this week, 1 = next week, -1 = last week, ...),
    returns the ISO week_key ('YYYY-Www') used for the week_key/week_start/
    week_end fields returned to the frontend. Reuses `_get_week_key_for_date`'s exact
    formatting so keys generated by the smart planner (weekly_slot actions)
    and keys generated here always line up."""
    target_date = _today_iran() + timedelta(weeks=week_offset)
    return f"{target_date.year}-W{target_date.isocalendar()[1]:02d}"


def _week_bounds_for_key(week_key: str) -> tuple[str, str]:
    """Returns (start_date_iso, end_date_iso) — Saturday through Friday, to
    match the Persian week used elsewhere in this file (_get_persian_day
    maps Saturday as the first day) — for a given 'YYYY-Www' key, so the
    frontend can show the date range above the grid."""
    year_str, week_str = week_key.split("-W")
    year, week = int(year_str), int(week_str)
    # ISO week's Monday, then shift back to the preceding Saturday to align
    # with the Persian week start used by _get_persian_day/PERSIAN_DAYS.
    iso_monday = date_type.fromisocalendar(year, week, 1)
    week_start = iso_monday - timedelta(days=2)  # Saturday
    week_end = week_start + timedelta(days=6)  # Friday
    return week_start.isoformat(), week_end.isoformat()


def _get_or_create_today_state(session, user_id: int) -> DailyState:
    """فقط برای mood/energy/notes (فیدبک روزانه) — تسک‌ها دیگر اینجا ذخیره نمی‌شن."""
    today = _today_str()
    state = session.query(DailyState).filter(
        DailyState.user_id == user_id, DailyState.date == today
    ).first()
    if not state:
        state = DailyState(user_id=user_id, date=today)
=======
    all_messages = [{"role": "system", "content": system_prompt}] + messages
    response = client.chat.completions.create(
        model=MODEL,
        messages=all_messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def _today_str() -> str:
    return date_type.today().isoformat()


def _current_week_key() -> str:
    today = date_type.today()
    return f"{today.year}-W{today.isocalendar()[1]:02d}"


def _get_or_create_today_state(session) -> DailyState:
    today = _today_str()
    state = session.query(DailyState).filter(DailyState.date == today).first()
    if not state:
        state = DailyState(date=today, current_tasks=json.dumps([]))
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
        session.add(state)
        session.commit()
        session.refresh(state)
    return state


<<<<<<< HEAD
def _dt_iso(x):
    return x.isoformat() if x else None


# ── Unified Task Store (Single Source of Truth) ────────────────────────────────
# همه‌ی تسک‌ها (چه «daily» چه «weekly») فقط در جدول رابطه‌ای TaskSlot
# ذخیره می‌شن (database.py) — هر اسلات یک ردیف مستقل با کلید یکتای
# (user_id, date, hour)، نه یک کلید داخل یک بلاب JSON مشترک. تفکیک
# daily/weekly صرفاً یک تفکیک UI-ئه: DailyView کوئریِ «آیتم‌های امروز» روی
# همین مخزنه و WeeklyView کوئری «آیتم‌های هفته» — دو نما از یک منبع، بدون
# dual-write و بدون هیچ تسک بی‌تاریخ یا بی‌ساعت (Zero Unscheduled Policy).
# get_context_for_llm (memory_manager.py) هم دقیقاً از همین جدول می‌خونه —
# یعنی چیزی که به مدل درباره‌ی «تسک‌های امروز» گفته می‌شه، همون چیزیه که
# صفحه‌ی Daily نشون می‌ده، نه یک کپی جدا که با LLM دیگه‌ای حدس زده شده.

def _json_list(v) -> list:
    if v is None:
        return []
    if isinstance(v, str):
        try:
            data = json.loads(v)
            return data if isinstance(data, list) else []
        except Exception:
            return []
    return v if isinstance(v, list) else []


def _slot_key(date_iso: str, hour: int) -> str:
    return f"{date_iso}|{int(hour)}"


def _parse_slot_key(key: str):
    try:
        date_part, hour_part = str(key).rsplit("|", 1)
        return date_part, int(hour_part)
    except ValueError:
        return None


def _normalize_schedule(raw, week_start_iso: str) -> dict:
    """
    خروجی همیشه دیکشنری استاندارد است:
        { "YYYY-MM-DD|H": {"text": str, "completed": bool} }
    فرمت قدیمی («شنبه-10»: «متن») با استفاده از شنبه‌ی همان هفته به کلید
    تاریخ‌دار تبدیل می‌شود تا داده‌های قبلی بدون migration خوانا بمانند.
    """
    result: dict = {}
    if not raw:
        return result
    data = json.loads(raw) if isinstance(raw, str) else raw
    if not isinstance(data, dict):
        return result
    try:
        week_start = date_type.fromisoformat(week_start_iso)
    except ValueError:
        return result
    legacy_offsets = {name: idx for idx, name in enumerate(PERSIAN_DAYS)}
    for key, val in data.items():
        parsed = _parse_slot_key(key)
        if parsed:
            d_iso, hour = parsed
            if isinstance(val, dict):
                item = {"text": str(val.get("text", "")), "completed": bool(val.get("completed"))}
            else:
                item = {"text": str(val), "completed": False}
        else:
            day_name, _, hour_s = str(key).rpartition("-")
            offset = legacy_offsets.get(day_name.strip())
            try:
                hour = int(hour_s)
            except ValueError:
                continue
            if offset is None or not (7 <= hour <= 23):
                continue
            d_iso = (week_start + timedelta(days=offset)).isoformat()
            item = {"text": str(val), "completed": False}
        if item["text"]:
            result[_slot_key(d_iso, hour)] = item
    return result


def _load_unified_items(session, user_id: int, anchor: date_type, window_days: int = 7) -> dict:
    """
    آیتم‌های TaskSlot را در یک بازه‌ی ±window_days روز اطراف anchor برمی‌گرداند
    (کلید «YYYY-MM-DD|HH» → {"text","completed"}) — همون شکل خروجی قبلی، ولی
    حالا مستقیماً یک کوئری range روی جدول ردیف‌محور TaskSlot است، نه merge چند
    بلاب JSON هفته‌ی ISO. همه‌ی caller های قبلی (که این دیکشنری رو با
    _day_items فیلتر می‌کنن) بدون تغییر کار می‌کنن.
    """
    start = (anchor - timedelta(days=window_days)).isoformat()
    end = (anchor + timedelta(days=window_days)).isoformat()
    rows = (
        session.query(TaskSlot)
        .filter(TaskSlot.user_id == user_id, TaskSlot.date >= start, TaskSlot.date <= end)
        .all()
    )
    return {_slot_key(r.date, r.hour): {"text": r.text, "completed": bool(r.completed)} for r in rows}


def _day_items(items: dict, date_iso: str) -> dict:
    prefix = date_iso + "|"
    return {k: v for k, v in items.items() if k.startswith(prefix)}


def _occupied_hours(session, user_id: int, d: date_type) -> set:
    day = _day_items(_load_unified_items(session, user_id, d), d.isoformat())
    return {_parse_slot_key(k)[1] for k in day}


def _first_free_hour(occupied_hours: set, preferred=None) -> int:
    """Autonomous Slot Filling: اول ساعت پیشنهادی (اگه آزاد)، بعد ساعت‌های
    کم‌بارِ شناختی (۱۰ و ۱۶)، بعد هر ساعت آزاد ۷ تا ۲۳."""
    candidates = ([preferred] if preferred is not None else []) + [10, 16] + list(range(7, 24))
    seen = set()
    for h in candidates:
        if h in seen or not (7 <= h <= 23):
            continue
        seen.add(h)
        if h not in occupied_hours:
            return h
    return 23


def _lock_item(session, user_id: int, d: date_type, hour: int, text: str, completed: bool = False) -> None:
    """
    Upsert روی یک ردیف TaskSlot (نه یک بلاب هفته). این تغییر دقیقاً همون
    race condition ای رو می‌بنده که با WeeklySchedule وجود داشت: قبلاً هر
    فراخوانی کل بلاب JSON هفته رو می‌خوند/می‌نوشت، پس دو تسک هم‌زمان (مثلاً
    یکی از چت، یکی از کلیک مستقیم تو صفحه‌ی Daily) می‌تونستن همدیگه رو با
    یه lost update پاک کنن. حالا هر اسلات یک ردیف مستقل با
    UniqueConstraint(user_id, date, hour) است؛ اگه بین SELECT و INSERT یه
    request دیگه دقیقاً همون اسلات رو گرفته باشه، DB با IntegrityError
    جلوش رو می‌گیره و اینجا به‌جای crash کردن، ردیف تازه‌اینسرت‌شده رو
    می‌خونیم و آپدیت می‌کنیم — هیچ داده‌ای گم نمی‌شه.
    `session.begin_nested()` (SAVEPOINT) استفاده شده تا اگه IntegrityError
    بخوره، فقط همین یک عملیات rollback بشه، نه بقیه‌ی تغییراتی که همین
    session تا الان جمع کرده (مثلاً وسط حلقه‌ی smart planner که چندتا
    تسک رو پشت‌سرهم قفل می‌کنه).
    """
    date_iso, hour = d.isoformat(), int(hour)
    row = (
        session.query(TaskSlot)
        .filter(TaskSlot.user_id == user_id, TaskSlot.date == date_iso, TaskSlot.hour == hour)
        .first()
    )
    if row:
        row.text = text
        row.completed = completed
        row.updated_at = datetime.utcnow()
        return
    try:
        with session.begin_nested():
            session.add(TaskSlot(user_id=user_id, date=date_iso, hour=hour, text=text, completed=completed))
    except IntegrityError:
        row = (
            session.query(TaskSlot)
            .filter(TaskSlot.user_id == user_id, TaskSlot.date == date_iso, TaskSlot.hour == hour)
            .first()
        )
        if row:
            row.text = text
            row.completed = completed
            row.updated_at = datetime.utcnow()


def _seed_today_if_empty(session, user_id: int) -> None:
    """اگر امروز هیچ آیتمی نداشته باشه، تودوهای اولیه (اهداف فعال) رو در
    اولین ساعت‌های منطقیِ آزاد قفل می‌کنه — بدون LLM، آنی. عادت‌ها اینجا
    seed نمی‌شن چون daily view همیشه به‌صورت زنده به لیست اضافه‌شون می‌کنه."""
    today = _today_iran()
    items = _load_unified_items(session, user_id, today)
    if _day_items(items, today.isoformat()):
        return
    goals = session.query(Goal).filter(Goal.user_id == user_id, Goal.status == "active").all()
    candidates = [g.title for g in goals if g.title]
    if not candidates:
        candidates = ["مرور برنامه امروز و اولویت‌بندی کارها"]
    occupied = {_parse_slot_key(k)[1] for k in _day_items(items, today.isoformat())}
    for text in candidates[:5]:
        hour = _first_free_hour(occupied)
        _lock_item(session, user_id, today, hour, text)
        occupied.add(hour)
=======
def _parse_tasks(state: DailyState) -> list[dict]:
    raw = state.current_tasks
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except Exception:
            return []
    else:
        data = raw
    result = []
    for idx, item in enumerate(data):
        if isinstance(item, str):
            result.append({"id": idx + 1, "text": item, "completed": False})
        elif isinstance(item, dict):
            result.append(item)
    return result


def _save_tasks(session, state: DailyState, tasks: list[dict]):
    state.current_tasks = json.dumps(tasks, ensure_ascii=False)
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    session.commit()


def _dt_iso(x):
    return x.isoformat() if x else None


<<<<<<< HEAD
# ── Robust JSON extraction for LLM output ───────────────────────────────────
# FIX (smart planner bug #1): Gemini's raw text output is not guaranteed to
# be strict JSON — even after stripping ```json fences it can contain
# trailing commas, smart quotes, or stray prose around the object, which
# makes a naive `json.loads(raw)` throw `Expecting property name enclosed in
# double quotes` and silently drop the whole extraction (the caller's
# try/except was swallowing it, so nothing ever landed in daily_tasks /
# weekly_schedule). This helper makes a few safe, progressively looser
# attempts before giving up, so real-but-slightly-malformed output still
# gets parsed instead of being discarded.
import re as _re


def _extract_json_object(raw: str) -> Optional[dict]:
    if not raw:
        return None
    text = raw.strip()

    # 1) strip ```json ... ``` or ``` ... ``` fences if present
    text = _re.sub(r"^```(?:json)?\s*", "", text)
    text = _re.sub(r"\s*```$", "", text).strip()

    if text.lower() in ("null", "none", ""):
        return None

    # 2) isolate the outermost {...} block in case the model added any
    #    leading/trailing prose around the JSON
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    # 3) try straightforward parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 4) common auto-repairs: trailing commas before } or ], smart quotes
    repaired = text
    repaired = repaired.replace("\u201c", '"').replace("\u201d", '"')
    repaired = repaired.replace("\u2018", "'").replace("\u2019", "'")
    repaired = _re.sub(r",\s*([}\]])", r"\1", repaired)  # trailing commas
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # 5) last resort: swap single quotes for double quotes. Only attempted
    #    if the string has no double quotes at all (to avoid mangling
    #    correctly-quoted JSON that failed for some other reason).
    if '"' not in repaired and "'" in repaired:
        swapped = _re.sub(r"'", '"', repaired)
        try:
            return json.loads(swapped)
        except json.JSONDecodeError:
            pass

    return None


def _recover_truncated_actions(raw: str) -> Optional[list]:
    """
    FIX (باگ اصلی «چیزی که تو چت می‌گم اصلاً وارد تقویم نمی‌شه»): گاهی
    Gemini خروجی رو وسط یه رشته یا شیء قطع می‌کنه (به max_tokens می‌خوره یا
    هر دلیل دیگه) — یعنی مثلاً `{"actions": [{"type": "daily_task", ...,
    "text": "تکمیل تمرین هو` بدون هیچ `}` بسته‌ای. توی این حالت
    _extract_json_object («تلاش برای پارس کامل») هیچ راهی نداره چون واقعاً
    چیزی برای پارس کامل نمونده — قبلاً این یعنی *کل* پیام (حتی اگه ۳-۴ تا
    اکشن قبلی‌ش کامل و سالم بودن) دور ریخته می‌شد.

    این تابع مستقل از _extract_json_object عمل می‌کنه: دنبال کلید
    "actions" می‌گرده، بعد با شمارش عمق آکولاد/کوتیشن (رشته‌آگاه، یعنی
    داخل رشته‌ها رو نادیده می‌گیره) هر شیء {...} که *کامل و بسته* شده رو
    جدا-جدا پارس می‌کنه. شیء نصفه‌ی آخر (همونی که قطع شده) به‌سادگی رد
    می‌شه، ولی هر چی قبلش کامل بوده نجات پیدا می‌کنه.
    """
    match = _re.search(r'"actions"\s*:\s*\[', raw)
    if not match:
        return None

    i = match.end()
    n = len(raw)
    depth = 0
    in_string = False
    escape = False
    obj_start = None
    objects: list = []

    while i < n:
        ch = raw[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                if depth == 0:
                    obj_start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and obj_start is not None:
                    chunk = raw[obj_start:i + 1]
                    try:
                        objects.append(json.loads(chunk))
                    except json.JSONDecodeError:
                        pass  # این شیء هم خودش ناقص بود — رد می‌شیم
                    obj_start = None
            elif ch == "]" and depth == 0:
                break
        i += 1

    return objects or None


=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
# FIX: updated to use correct field names matching database.py
def worktask_to_dict(t: WorkTask):
    return {
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "due_at": _dt_iso(t.due_at),
        "estimated_pomodoros": t.estimated_pomodoros,
        "completed_pomodoros": t.completed_pomodoros,
        "current_progress": t.current_progress,
        "difficulty": t.difficulty,
        "cognitive_load": t.cognitive_load,
        "cognitive_intensity": t.cognitive_intensity,
        "mental_fatigue": t.mental_fatigue,
        "focus_requirements": t.focus_requirements,
        "status": t.status,
        "extra_metadata": t.extra_metadata,
        "created_at": _dt_iso(t.created_at),
        "updated_at": _dt_iso(t.updated_at),
    }


# FIX: updated to use correct field names matching database.py
def reminder_to_dict(r: Reminder):
    return {
        "id": r.id,
        "title": r.title,
        "message": r.message,
        "reminder_at": _dt_iso(r.reminder_at),
        "reminder_type": r.reminder_type,
        "sent": r.sent,
        "priority": r.priority,
        "language": r.language,
        "rtl": r.rtl,
        "avatar_emotion": r.avatar_emotion,
        "extra_metadata": r.extra_metadata,
        "created_at": _dt_iso(r.created_at),
        "updated_at": _dt_iso(r.updated_at),
    }


def pomodoro_to_dict(p: PomodoroSession):
    return {
        "id": p.id,
        "task_id": p.task_id,
        "session_type": p.session_type,
        "start_time": _dt_iso(p.start_time),
        "end_time": _dt_iso(p.end_time),
        "duration_minutes": p.duration_minutes,
        "status": p.status,
        "created_at": _dt_iso(p.created_at),
        "updated_at": _dt_iso(p.updated_at),
    }


# ── Morning Initialization Protocol ───────────────────────────────────────────

<<<<<<< HEAD
async def _morning_init_if_needed(user_id: int) -> bool:
    """
    بررسی می‌کند آیا DailyState امروز برای این کاربر وجود دارد یا خیر.
    اگر نه، یک لیست تودوی اولیه می‌سازد.

    FIX (bug #3 — دوبار صدا زدن Gemini توی اولین چت صبح): قبلاً این تابع
    خودش یک بار Gemini را برای تولید تودوهای شخصی‌سازی‌شده صدا می‌زد و
    *بعد* هم چت اصلی یک بار دیگر Gemini را صدا می‌زد — یعنی اولین پیام
    هر روز کاربر، دو برابر طول می‌کشید (۳ تا ۶ ثانیه بیشتر). حالا این
    تابع کاملاً بدون LLM و آنی کار می‌کند: تودوهای اولیه را مستقیماً از
    روی اهداف/عادت‌های فعال کاربر می‌سازد (rule-based، نه Gemini). اگر
    کاربر هیچ هدف/عادتی ثبت نکرده باشد، چند تودوی عمومی پیش‌فرض می‌گذارد.
    این لیست بعداً هم قابل ویرایش/جایگزینی توسط خود کاربر یا smart planner
    است — فقط دیگر مسیر بحرانی (critical path) چت را کند نمی‌کند.
=======
async def _morning_init_if_needed() -> bool:
    """
    بررسی می‌کند آیا DailyState امروز وجود دارد یا خیر.
    اگر نه، تودوهای شخصی‌سازی‌شده از طریق GapGPT می‌سازد.
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    True برمی‌گرداند اگر اولین تعامل روز بود.
    """
    session = get_session()
    try:
<<<<<<< HEAD
        today_iso = _today_str()
        items = _load_unified_items(session, user_id, _today_iran())
        had_tasks = bool(_day_items(items, today_iso))
        if not had_tasks:
            _seed_today_if_empty(session, user_id)
        return not had_tasks
=======
        today = _today_str()
        state = session.query(DailyState).filter(DailyState.date == today).first()

        if state and state.current_tasks:
            raw = state.current_tasks
            tasks = json.loads(raw) if isinstance(raw, str) else raw
            if tasks:
                return False

        goals = session.query(Goal).filter(Goal.status == "active").all()
        habits = session.query(Habit).filter(Habit.is_active == True).all()

        goals_text = "\n".join(
            [f"- {g.title} ({g.category or 'عمومی'})" for g in goals]
        ) or "هیچ هدف فعالی ثبت نشده"
        habits_text = "\n".join(
            [f"- {h.name} ({h.frequency})" for h in habits]
        ) or "هیچ عادتی ثبت نشده"

        system = "تو یک برنامه‌ریز هوشمند هستی. فقط JSON خالص برمی‌گردانی، بدون هیچ توضیح یا markdown."
        user_prompt = f"""تاریخ امروز: {today}
اهداف فعال کاربر:
{goals_text}

عادت‌های روزانه:
{habits_text}

یک لیست تودوی شخصی‌سازی‌شده برای امروز بساز.
فقط یک آرایه JSON از رشته‌های فارسی برگردان. مثال:
["مطالعه ۳۰ دقیقه ریاضی گسسته", "ورزش صبح", "مرور فلش‌کارت‌های زیست"]
فقط JSON، بدون توضیح اضافه، بدون کد بلاک."""

        loop = asyncio.get_event_loop()
        raw_text = await loop.run_in_executor(
            None,
            lambda: _call_llm(
                system,
                [{"role": "user", "content": user_prompt}],
                temperature=0.5,
                max_tokens=500,
            ),
        )

        raw_text = raw_text.strip().replace("```json", "").replace("```", "").strip()
        task_list = json.loads(raw_text)

        tasks_structured = [
            {"id": idx + 1, "text": t, "completed": False}
            for idx, t in enumerate(task_list)
            if isinstance(t, str)
        ]

        if state:
            state.current_tasks = json.dumps(tasks_structured, ensure_ascii=False)
            session.commit()
        else:
            new_state = DailyState(
                date=today,
                current_tasks=json.dumps(tasks_structured, ensure_ascii=False),
            )
            session.add(new_state)
            session.commit()

        return True

>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    except Exception as e:
        print(f"⚠️ morning init failed: {e}")
        return False
    finally:
        session.close()


# ── Endpoints ──────────────────────────────────────────────────────────────────

<<<<<<< HEAD
# ── Onboarding (multi-user) ─────────────────────────────────────────────────
# NOTE: this is the replacement for what seed_data.py used to do globally —
# each new user fills this in themselves (via the frontend wizard) instead
# of inheriting one hardcoded persona.

@app.post("/api/onboarding")
async def complete_onboarding(payload: OnboardingRequest, current_user: User = Depends(get_current_user)):
    mm = MemoryManager(user_id=current_user.id)
    mm.update_persona(
        preferred_name=payload.preferred_name,
        age=payload.age,
        occupation=payload.occupation,
        education_level=payload.education_level,
        life_philosophy=payload.life_philosophy,
        core_values=payload.core_values,
    )
    mm.update_psychology(
        communication_style=payload.learning_style,
        stress_triggers=payload.main_challenges,
        motivators=payload.motivators,
    )
    session = get_session()
    try:
        user = session.get(User, current_user.id)
        user.onboarding_completed = True
        if payload.preferred_name and not user.display_name:
            user.display_name = payload.preferred_name
        session.commit()
    finally:
        session.close()
    return {"status": "success", "onboarding_completed": True}


@app.get("/")
async def root():
    return {
        "status": "running",
        "assistant": "Jarvis-You",
=======
@app.get("/")
async def root():
    persona = memory_manager.get_persona()
    return {
        "status": "running",
        "assistant": "Jarvis-You",
        "user": persona.get("preferred_name", "کاربر"),
        "session_id": SESSION_ID,
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
        "llm": MODEL,
    }


@app.post("/api/chat", response_model=ChatResponse)
<<<<<<< HEAD
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    memory_manager = MemoryManager(user_id=current_user.id, session_id=PROCESS_SESSION_ID)
    try:
        # ── لایه‌ی ۵ داربست شناختی (حلقه‌ی بسته) ────────────────────────────
        # قبل از هرچیز دیگه، ببین آیا این پیام جواب کاربر به یه سوال
        # بازتابی قبلیه که واقعاً باورشو اصلاح می‌کنه. اگه آره، توی
        # BeliefRevision لاگ می‌شه و Psychology به‌روز می‌شه — بی‌صدا، بدون
        # این‌که جریان معمول پاسخ رو قطع کنه.
        belief_revision = memory_manager.check_belief_revision(request.message, llm_client=client)
        if belief_revision:
            print(f"🔄 belief revised for user {current_user.id}: {belief_revision['field_name']}")

        # ── تأیید/رد پیشنهاد مطالعه‌ی مطرح‌شده در پیام قبلی ──────────────────
        # اگه smart planner پیام قبلش یه بلوک مطالعه پیشنهاد داده بود و
        # کاربر الان تأیید/رد کرد، همین‌جا حلقه بسته می‌شه.
        plan_action, plan_items = None, []
        plan_session = get_session()
        try:
            plan_action, plan_items = _consume_pending_plan(plan_session, current_user.id, request.message)
        finally:
            plan_session.close()
        locked_blocks = []
        if plan_action == "approved":
            lock_session = get_session()
            try:
                locked_blocks = _apply_plan_items(lock_session, current_user.id, plan_items or [])
            finally:
                lock_session.close()

        is_morning_init = await _morning_init_if_needed(current_user.id)

        system_prompt = build_system_prompt(memory_manager)

        if is_morning_init:
            preview_session = get_session()
            try:
                _seed_today_if_empty(preview_session, current_user.id)
                day = _day_items(
                    _load_unified_items(preview_session, current_user.id, _today_iran()),
                    _today_str(),
                )
                entries = sorted(
                    (_parse_slot_key(k)[1], v["text"]) for k, v in day.items()
                )
                tasks_preview = "، ".join(text for _, text in entries[:3])
            finally:
                preview_session.close()
=======
async def chat(request: ChatRequest):
    try:
        is_morning_init = await _morning_init_if_needed()

        system_prompt = build_system_prompt()

        if is_morning_init:
            session = get_session()
            try:
                state = session.query(DailyState).filter(
                    DailyState.date == _today_str()
                ).first()
                tasks_raw = state.current_tasks if state else "[]"
                tasks = json.loads(tasks_raw) if isinstance(tasks_raw, str) else tasks_raw
                task_titles = [t["text"] for t in tasks if isinstance(t, dict)]
                tasks_preview = "، ".join(task_titles[:3])
            finally:
                session.close()
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9

            system_prompt += (
                f"\n\n---\nMORNING INIT: امروز اولین تعامل روز است. "
                f"تودوهای زیر برای کاربر تولید شده‌اند: {tasks_preview}. "
                "یک خوش‌آمدگویی صبحگاهی گرم، شخصی و انگیزه‌بخش بده. "
                "به طور خاص به اهداف و برنامه‌های امروز اشاره کن. "
                "پیام کوتاه، صمیمی و محرک باشد."
            )

<<<<<<< HEAD
        # ── Behavioral reflection (cognitive scaffolding) ────────────────────
        # اگه scheduler_service.py یه تناقض معنادار بین رفتار عینی کاربر و
        # پروفایل self-reported پیدا کرده باشه، اینجا فقط یک‌بار مصرفش
        # می‌کنیم (consume پاکش می‌کنه) و به جارویس می‌گیم طبیعی مطرحش کنه —
        # نه به‌عنوان یه لیست جدا، بلکه بافته‌شده توی همون جواب.
        pending_reflection = memory_manager.consume_pending_reflection()
        if pending_reflection:
            system_prompt += (
                f"\n\n---\nREFLECTION PROMPT (فقط یک‌بار، طبیعی و بدون قضاوت مطرح کن): "
                f"{pending_reflection}"
            )

=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
        history = memory_manager.get_conversation_history()
        messages = build_chat_history(history)
        messages.append({"role": "user", "content": request.message})

        loop = asyncio.get_event_loop()
        assistant_message = await loop.run_in_executor(
            None,
            lambda: _call_llm(system_prompt, messages, temperature=0.7, max_tokens=1500),
        )

        memory_manager.add_conversation(request.message, assistant_message)
<<<<<<< HEAD
        asyncio.create_task(_async_memory_update(current_user.id, request.message, assistant_message))

        # ── Smart Planner: پشت‌پرده اجرا و نتیجه به پاسخ اضافه می‌شه
        planner_actions = await _async_smart_planner(current_user.id, request.message, assistant_message)

        # ── تأیید صریح قفل‌شدن اسلات‌ها (Zero Unscheduled Policy) ────────────
        locked_lines: list = []
        proposal_blocks: list = []
        for a in planner_actions:
            if a["type"] == "proposal":
                proposal_blocks = a.get("blocks", [])
            elif a["type"] == "weekly_recurring":
                locked_lines.append(
                    f"• هر هفته، {a['day']} ساعت {int(a['hour']):02d}:۰۰ — {a['text']} "
                    f"(برای {a['weeks']} هفته ثبت شد)"
                )
            elif a["type"] == "habit":
                hour_txt = f" ساعت {int(a['hour']):02d}:۰۰" if a.get("hour") else ""
                locked_lines.append(f"• عادت روزانه ثبت شد: {a['text']}{hour_txt}")
            elif a["type"] in ("daily", "study_block"):
                locked_lines.append(
                    f"• {a['day']} {a['date']} ساعت {int(a['hour']):02d}:۰۰ — {a['text']}"
                )
            elif a["type"] == "weekly":
                locked_lines.append(
                    f"• هر هفته، {a['day']} ساعت {int(a['hour']):02d}:۰۰ — {a['text']}"
                )

        if plan_action == "approved":
            if locked_blocks:
                for b in locked_blocks:
                    locked_lines.append(
                        f"• {b['day']} {b['date']} ساعت {int(b['hour']):02d}:۰۰ — {b['text']}"
                    )

        note_parts: list = []
        if locked_lines:
            note_parts.append("\n\n---\n🔒 قفل شد در برنامه‌ات:")
            note_parts.extend(locked_lines)
        if plan_action == "approved" and not locked_blocks:
            note_parts.append("\n\n---\n✅ پیشنهاد قبلی تأیید شد (اسلات‌ها پر بودن یا قبلاً ثبت شده بودن).")
        if proposal_blocks:
            note_parts.append("\n\n---\n🧩 پیشنهاد برنامه‌ریزی مطالعه (منتظر تأیید تو):")
            for b in proposal_blocks:
                d = date_type.fromisoformat(b["date"])
                note_parts.append(
                    f"• {_get_persian_day(d)} {b['date']} ساعت {int(b['hour']):02d}:۰۰ — {b['text']} (~۲ پومودورو)"
                )
            note_parts.append(
                "اگه تأیید می‌کنی فقط بنویس «تأیید» تا همه رو قفل کنم توی تقویم؛ اگه نمی‌خوای بنویس «نه»."
            )
        if note_parts:
            assistant_message += "\n".join(note_parts)

        return ChatResponse(response=assistant_message, session_id=PROCESS_SESSION_ID)

    except HTTPException:
        raise
    except LLMUnavailableError as e:
        # FIX (bug #2): dedicated 429 instead of a bare 500, with a message
        # the frontend can show as-is.
        raise HTTPException(status_code=429, detail=str(e))
=======
        asyncio.create_task(_async_memory_update(request.message, assistant_message))

        # ── Smart Planner: پشت‌پرده اجرا و نتیجه به پاسخ اضافه می‌شه
        planner_actions = await _async_smart_planner(request.message, assistant_message)
        if planner_actions:
            note_lines = ["\n\n---\n📅 ثبت شد در برنامه‌ات:"]
            for a in planner_actions:
                if a["type"] == "daily":
                    note_lines.append(f"• روز {a['day']} ({a['date']}): {a['text']}")
                elif a["type"] == "weekly":
                    note_lines.append(f"• برنامه هفتگی {a['day']} ساعت {a['hour']}: {a['text']}")
            assistant_message += "\n".join(note_lines)

        return ChatResponse(response=assistant_message, session_id=SESSION_ID)

>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    except Exception as e:
        print(f"🔥 ارور بک‌اند: {e}")
        raise HTTPException(status_code=500, detail=f"خطا در پردازش: {str(e)}")


<<<<<<< HEAD
async def _async_memory_update(user_id: int, user_msg: str, assistant_msg: str):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _sync_memory_update, user_id, user_msg, assistant_msg)


def _sync_memory_update(user_id: int, user_msg: str, assistant_msg: str):
    try:
        mm = MemoryManager(user_id=user_id, session_id=PROCESS_SESSION_ID)
=======
async def _async_memory_update(user_msg: str, assistant_msg: str):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _sync_memory_update, user_msg, assistant_msg)


def _sync_memory_update(user_msg: str, assistant_msg: str):
    try:
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
        updates = extract_memory_updates(
            client=client,
            user_message=user_msg,
            assistant_message=assistant_msg,
<<<<<<< HEAD
            current_memory=mm.memory,
        )
        if updates:
            mm.update_memory_fields(updates)
=======
            current_memory=memory_manager.memory,
        )
        if updates:
            memory_manager.update_memory_fields(updates)
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
            print(f"✅ memory updated: {list(updates.keys())}")
    except Exception as e:
        print(f"⚠️ memory update failed (non-critical): {e}")


# ── Smart Planner: استخراج task/deadline از چت ────────────────────────────────

PLANNER_EXTRACT_PROMPT = """
تو یک سیستم استخراج برنامه‌ریزی هستی.
امروز: {today} ({today_fa})
<<<<<<< HEAD
روزهای هفته به فارسی به ترتیب: شنبه، یکشنبه، دوشنبه، سه‌شنبه، چهارشنبه، پنجشنبه، جمعه

از این مکالمه، هر task یا برنامه‌ی زمان‌بندی‌شده‌ای که هست استخراج کن — شامل
موعدهای آینده مثل امتحان، تحویل تمرین، جلسه، کلاس و غیره، چه مال همین هفته
باشن چه هفته‌های بعد.
مهم: اگر پیام دستیار شامل یک برنامه‌ی چندآیتمی است (مثلاً چند خط با ساعت‌های
مختلف، حتی زیر یک تیتر مثل «برنامه‌ی امروز» یا «پیش‌نویس فردا»)، باید همه‌ی
آیتم‌ها را جداگانه استخراج کنی — نه فقط اولی را.

کاربر: {user_message}
دستیار: {assistant_message}

اگر هیچ task یا برنامه‌ای نیست: فقط بنویس null

اگر هست، JSON زیر را برگردان. توجه: تاریخ دقیق را خودت محاسبه نکن — به‌جاش
فقط بگو «کدوم روز هفته»، «چند هفته جلوتر» یا «چند روز از امروز»، کد از رویش
تاریخ دقیق رو حساب می‌کنه (چون محاسبه‌ی دستی تاریخ توسط مدل خطاپذیره):

=======
روزهای هفته به فارسی: شنبه، یکشنبه، دوشنبه، سه‌شنبه، چهارشنبه، پنجشنبه، جمعه

از این مکالمه، task یا deadline استخراج کن:
کاربر: {user_message}
دستیار: {assistant_message}

اگر هیچ task یا deadline‌ای نیست: فقط بنویس null

اگر هست، JSON زیر را برگردان:
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
{{
  "actions": [
    {{
      "type": "daily_task",
<<<<<<< HEAD
      "day": "سه‌شنبه",
      "week_offset": 1,
      "hour": 10,
      "text": "متن تسک به فارسی، بدون تکرار ساعت توی متن (ساعت جدا توی فیلد hour میاد)"
    }},
    {{
      "type": "daily_task",
      "days_from_now": 3,
      "hour": 10,
      "text": "برای «N روز دیگه» — day/week_offset نذار"
=======
      "date": "YYYY-MM-DD",
      "text": "متن تسک به فارسی"
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    }},
    {{
      "type": "weekly_slot",
      "day": "شنبه",
<<<<<<< HEAD
      "week_offset": 0,
      "recurring": true,
      "hour": 14,
      "text": "برنامه‌ای که هر هفته تکرار می‌شه"
    }},
    {{
      "type": "habit",
      "hour": 7,
      "text": "عادت روزانه‌ای که هر روز تکرار می‌شه"
=======
      "hour": 14,
      "text": "متن برنامه به فارسی"
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    }}
  ]
}}

<<<<<<< HEAD
راهنمای پر کردن "day" و "week_offset" (این دو تا همیشه با هم می‌آن، به‌جای date خام):
- «امروز» → day = {today_fa}، week_offset = 0
- «فردا» → day = روز بعدِ {today_fa} در چرخه‌ی هفته، week_offset = 0 (یا 1 اگه فردا از جمعه رد بشه به شنبه‌ی هفته‌ی بعد)
- «سه‌شنبه» (بدون «هفته‌ی بعد») → day = "سه‌شنبه"، week_offset = 0 — کد خودش اگه اون روز از این هفته گذشته باشه، خودکار می‌بره هفته‌ی بعد
- «سه‌شنبه‌ی هفته‌ی بعد» / «سه‌شنبه هفته دیگه» → day = "سه‌شنبه"، week_offset = 1
- «دو هفته‌ی دیگه سه‌شنبه» → day = "سه‌شنبه"، week_offset = 2
- به همین ترتیب برای «سه هفته دیگه» → week_offset = 3

راهنمای پر کردن "days_from_now" (برای عبارت‌های شمارشی «N روز دیگه»):
- «سه روز دیگه ساعت ۱۰ امتحان دارم» → type = daily_task با days_from_now = 3 (بدون day و week_offset)
- «فردا» هم می‌تونه days_from_now = 1 باشه؛ ولی «پس‌فردا» حتماً days_from_now = 2
- days_from_now باید عدد صحیح بزرگ‌تر یا مساوی صفر باشه؛ تاریخ رو خودت جمع نزن

تفکیک سه حاله (خیلی مهم):
- «فردا امتحان دارم» / «سه‌شنبه کلاس دارم» / «ده روز دیگه تحویل پروژه‌ست» → رویداد یک‌باره: daily_task (با day+week_offset یا days_from_now)
- «هر شنبه کلاس دارم» / «هر هفته دوشنبه جلسه‌م» → تکرار هفتگی: weekly_slot با recurring = true و day = اسم روز (کد خودش چند هفته‌ی جلوتر رو پر می‌کنه)
- «هر روز پیاده‌روی می‌رم» / «هر روز ساعت ۷ مطالعه می‌کنم» → عادت روزانه: type = habit (بدون day و week_offset)

راهنمای پر کردن "hour" (این فیلد برای daily_task هم مثل weekly_slot اجباریه — هیچ تسکی نباید بدون ساعت بمونه):
- اگه کاربر ساعت مشخصی گفته («ساعت ۱۰»، «۱۵:۳۰ تا ۱۶:۳۰») → همون ساعتِ شروع رو بذار
- اگه دستیار توی پاسخ خودش یه ساعت مشخص برای این تسک پیشنهاد داده بود (مثلاً «این رو برای ساعت ۱۰ گذاشتم») → همون ساعت رو بذار
- اگه هیچ‌کدوم ساعتی نگفتن → همین فیلد رو کلاً حذف کن یا null بذار؛ سیستم خودش یه ساعت خالی و منطقی انتخاب می‌کنه (نگران نباش، هیچ تسکی بدون ساعت توی تقویم نهایی نمی‌مونه)

قوانین:
- اگر کاربر صرفاً دارد برنامه‌ای را که قبلاً در پیام‌های اخیر همین گفتگو مطرح یا تأیید شده تکرار می‌کند یا صرفاً درباره‌اش صحبت می‌کند، مجدداً آن را به عنوان اکشن جدید استخراج نکن — مگر اینکه کاربر صراحتاً ساعت یا روز آن را تغییر داده باشد (که در این صورت فقط همان نسخه‌ی تغییر یافته با day/hour جدید برگردد).
- برای برنامه‌ی مربوط به «امروز» یا یک روز مشخص (حتی چند آیتم پشت‌سرهم با ساعت‌های مختلف): هرکدوم رو یه daily_task جدا بساز.
- برای deadline (مثلاً «سه‌شنبه‌ی هفته‌ی بعد امتحان دارم» یا «باید تمرین تحویل بدم»): یک daily_task برای «روز قبل از deadline» بساز با متن «مرور و آماده‌سازی: [موضوع]» (week_offset رو با توجه به اینکه یه روز عقب‌تره حساب کن)، و یک daily_task دیگه هم برای خودِ روز deadline با متن خودِ موضوع (مثلاً «امتحان [درس]» یا «تحویل تمرین [درس]»).
- برای برنامه‌ی هفتگی/تکرارشونده با نام روز هفته مشخص که قراره هرهفته تکرار بشه (نه یه رویداد یک‌باره مثل امتحان): weekly_slot با recurring = true بساز — فقط اگه کاربر صراحتاً «هر شنبه/هر هفته» گفته، نه برای یه کلاس یا جلسه‌ی تک‌بار.
- برای رفتار تکرارشونده‌ی هرروزه («هر روز ورزش می‌کنم»): type = habit با hour (اگه ساعت گفته بود) و text = اسم کوتاه عادت.
- hour باید عدد صحیح بین 7 تا 23 باشد (اگه معلوم نیست، حذفش کن، منفی یا رشته نذار)
- اگر پیش‌نویس/برنامه‌ی «فردا» یا روزی که هنوز نرسیده را می‌بینی، همون رو هم به‌عنوان daily_task ثبت کن (نه فقط چیزهای همین امروز)
- فقط JSON خالص یا null، بدون توضیح، بدون markdown fence (```)، بدون کاما اضافه قبل از }} یا ]
- همه‌ی کلیدها و مقادیر رشته‌ای باید داخل دابل‌کوتیشن (") باشند، نه تک‌کوتیشن
=======
قوانین:
- برای deadline (مثلاً «شنبه تکلیف شبکه دارم»): یک daily_task برای روز قبل از deadline بساز با متن «مرور و آماده‌سازی: [موضوع]» و یک weekly_slot برای روز deadline با ساعت مناسب
- برای task امروز یا فردا: فقط daily_task
- برای برنامه هفتگی خاص: فقط weekly_slot
- hour باید عدد صحیح بین 7 تا 23 باشد
- date باید از امروز به بعد باشد
- فقط JSON خالص یا null، بدون توضیح
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
"""

PERSIAN_DAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]


<<<<<<< HEAD
def _normalize_persian(text: str) -> str:
    """
    FIX: مدل همیشه نیم‌فاصله (ZWNJ) رو رعایت نمی‌کنه — «سه‌شنبه» توی
    PERSIAN_DAYS با نیم‌فاصله تعریف شده ولی Gemini گاهی «سه شنبه» (با
    فاصله‌ی معمولی) یا حتی بدون فاصله برمی‌گردونه. چون قبلاً هیچ نرمال‌سازی‌ای
    نبود، `day_name not in PERSIAN_DAYS` بی‌صدا True می‌شد و کل action (بدون
    هیچ لاگی) دور ریخته می‌شد. همچنین ي/ك عربی رو به ی/ک فارسی تبدیل می‌کنه.
    """
    if not text:
        return ""
    text = text.replace("ي", "ی").replace("ك", "ک")
    text = text.replace("سه شنبه", "سه‌شنبه").replace("پنج شنبه", "پنجشنبه").replace("پنج‌شنبه", "پنجشنبه")
    return text.strip()


# ── Smart Task Deduplication ────────────────────────────────────────────────
# FIX (task duplication): قبلاً چک تکراری بودن فقط تطابق ۱۰۰٪ کلمه‌به‌کلمه
# بود؛ چون متنِ استخراج‌شده توسط مدل در هر بار فرق می‌کرد («مطالعه ریاضی
# گسسته» vs «درس ریاضی گسسته (ساعت ۱۰:۰۰)») هر بار یک آیتم جدید ساخته می‌شد.
# الان هسته‌ی معنایی متن (فینگرپرینت) مقایسه می‌شود: اگر برای همان تاریخ
# آیتمی با هسته‌ی مشابه وجود داشته باشد، به‌جای ساخت ردیف جدید، همان آیتم
# آپدیت می‌شود.

_TASK_STOPWORDS = frozenset([
    "و", "در", "به", "از", "که", "را", "با", "تا", "برای", "هم", "می",
    "یک", "یکی", "دوباره", "دیگه", "دیگر", "کنم", "کن", "بکن", "دارم",
    "داره", "است", "هست", "بود", "شه", "بشه", "ساعت", "ساعتی",
])


def _task_fingerprint(text: str) -> frozenset:
    """
    متن تسک را به مجموعه‌ای از کلمات کلیدی نرمال‌شده تبدیل می‌کند تا دو
    صیغه‌ی متفاوت از یک کار («مطالعه ریاضی گسسته» / «درس ریاضی گسسته
    (ساعت ۱۰)») فینگرپرینت یکسان بگیرند:
      - ی/ك عربی → فارسی، حذف علائم و پرانتزها، حذف اعداد/ساعت‌ها
      - نیم‌فاصله → فاصله (تا «سه‌شنبه» و «سه شنبه» برابر شوند)
      - حذف کلمات ایست پرتکرار که هیچ بار معنایی ندارند
    """
    t = _normalize_persian(str(text)).lower()
    t = _re.sub(r"\([^)]*\)", " ", t)              # پرانتزها («(ساعت ۱۰)»)
    t = _re.sub(r"[0-9۰-۹]+", " ", t)              # اعداد فارسی/لاتین
    t = _re.sub(r"[\u200c\u200e\u200f]", " ", t)   # ZWNJ و کنترل‌کاراکترها
    t = _re.sub(r"[^\w\u0600-\u06FF\s]", " ", t)   # علائم سجاوندی
    words = {w for w in t.split() if len(w) > 1 and w not in _TASK_STOPWORDS}
    return frozenset(words)


def _fingerprints_match(a: frozenset, b: frozenset, threshold: float = 0.6) -> bool:
    """تشخیص تشابه بر اساس هم‌پوشانی کلمات کلیدی (containment). آستانه‌ی
    0.6 یعنی حداقل ~۶۰٪ کلماتِ متن کوتاه‌تر باید مشترک باشد — برای تیترهای
    کوتاه تسک عملاً یعنی «همان کار»."""
    if not a or not b:
        return False
    if a == b:
        return True
    overlap = len(a & b)
    return (overlap / min(len(a), len(b))) >= threshold


def _dedup_upsert_item(session, user_id: int, d: date_type, hour_hint, text: str):
    """
    ضدتکرار هوشمند برای مخزن یکپارچه:
      a) اگر برای تاریخ d آیتمی با فینگرپرینت مشابه وجود داشته باشد → همان
         آیتم آپدیت می‌شود (وضعیت completed و ساعت قبلی‌اش حفظ می‌شود).
      b) وگرنه مثل قبل اولین اسلات منطقی خالی (ترجیحاً hour_hint) قفل می‌شود.
    خروجی: (assigned_hour, updated_existing)
    """
    fp_new = _task_fingerprint(text)

    day_items = _day_items(_load_unified_items(session, user_id, d), d.isoformat())
    for k, v in day_items.items():
        parsed = _parse_slot_key(k)
        if not parsed:
            continue
        if _fingerprints_match(fp_new, _task_fingerprint(v.get("text", ""))):
            h_existing = parsed[1]
            # UPDATE نه INSERT — متن تازه جایگزین می‌شود، ردیف تکراری ساخته نمی‌شود
            _lock_item(session, user_id, d, h_existing, text,
                       completed=bool(v.get("completed")))
            return h_existing, True

    occupied = {_parse_slot_key(k)[1] for k in day_items}
    try:
        hint = int(hour_hint) if hour_hint is not None else None
    except (TypeError, ValueError):
        hint = None
    if hint is not None and 7 <= hint <= 23 and hint not in occupied:
        assigned = hint
    else:
        assigned = _first_free_hour(occupied, preferred=hint)
    _lock_item(session, user_id, d, assigned, text)
    return assigned, False


=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
def _get_persian_day(d: date_type) -> str:
    wd = d.weekday()  # Mon=0..Sun=6
    mapping = {5: 0, 6: 1, 0: 2, 1: 3, 2: 4, 3: 5, 4: 6}  # Sat=شنبه
    return PERSIAN_DAYS[mapping[wd]]


def _get_week_key_for_date(d: date_type) -> str:
    return f"{d.year}-W{d.isocalendar()[1]:02d}"


<<<<<<< HEAD
def _resolve_action_date(action: dict, today: date_type) -> Optional[date_type]:
    """
    تاریخ دقیق یک action رو محاسبه می‌کنه — به‌جای اینکه از مدل بخوایم خودش
    تاریخ (YYYY-MM-DD) حساب کنه، که برای مدل خطاپذیره. دو مسیر پشتیبانی می‌شه:
      1) days_from_now («سه روز دیگه») → امروز + N روز — دقیق و بدون هیچ
         حدس weekday-ای از سمت مدل.
      2) day (نام فارسی روز) + week_offset — مثل قبل.

    اگه week_offset صفر باشه و اون روز از هفته‌ی جاری از امروز گذشته باشه
    (مثلاً امروز چهارشنبه‌ست و کاربر گفته «دوشنبه» بدون هیچ قید هفته‌ای)،
    خودکار می‌ره سراغ همون روز در هفته‌ی بعد — چون منظور کاربر از یه روزِ
    گذشته، تقریباً همیشه دوشنبه‌ی آینده‌ست، نه یه تاریخ در گذشته.
    """
    # مسیر ۱: شمارش مستقیم روزها («N روز دیگه» / «پس‌فردا») — اولویت داره.
    raw_dfn = action.get("days_from_now")
    if raw_dfn is not None:
        try:
            dfn = int(raw_dfn)
        except (TypeError, ValueError):
            dfn = None
        if dfn is not None and 0 <= dfn <= 365:
            return today + timedelta(days=dfn)

    day_name = _normalize_persian(action.get("day", ""))
    if day_name not in PERSIAN_DAYS:
        print(f"⚠️ smart planner: day '{action.get('day')}' (normalized: '{day_name}') not in PERSIAN_DAYS — action dropped")
        return None

    try:
        week_offset = int(action.get("week_offset", 0) or 0)
    except (TypeError, ValueError):
        week_offset = 0
    week_offset = max(0, week_offset)  # منفی معنی نداره، امن‌سازی

    today_idx = PERSIAN_DAYS.index(_get_persian_day(today))
    week_start = today - timedelta(days=today_idx)  # شنبه‌ی همین هفته

    target_idx = PERSIAN_DAYS.index(day_name)
    target_date = week_start + timedelta(weeks=week_offset, days=target_idx)

    if week_offset == 0 and target_date < today:
        # اون روز از این هفته گذشته و هیچ هفته‌ی جلوتری هم مشخص نشده —
        # پس منظور همون روز در هفته‌ی بعده.
        target_date += timedelta(weeks=1)

    return target_date


def _sync_smart_planner(user_id: int, user_msg: str, assistant_msg: str) -> list:
    # FIX (bug #4): use Iran-local "today", not UTC server today — otherwise
    # tasks extracted near midnight (Iran time) get filed under the wrong
    # date/weekday.
    today = _today_iran()
=======
def _sync_smart_planner(user_msg: str, assistant_msg: str) -> list:
    today = date_type.today()
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    today_fa = _get_persian_day(today)

    prompt = PLANNER_EXTRACT_PROMPT.format(
        today=today.isoformat(),
        today_fa=today_fa,
        user_message=user_msg,
<<<<<<< HEAD
        # FIX: 400 chars was truncating any real multi-item schedule
        # mid-sentence (a plan with 4-5 timed items easily runs past that),
        # so the extractor either saw garbage or returned null. Gemini
        # Flash has plenty of context room — 3000 chars is generous enough
        # for a full daily/weekly plan without meaningfully raising cost.
        assistant_message=assistant_msg[:3000],
=======
        assistant_message=assistant_msg[:400],
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "فقط JSON خالص یا null برمی‌گردانی."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
<<<<<<< HEAD
            # FIX: 600 → 1500 → 2200. حتی 1500 هم برای پیام‌هایی با چندتا
            # آیتم (هرکدوم با day/week_offset/hour/text) گاهی وسط کار قطع
            # می‌شد — لاگ‌های واقعی همینو نشون دادن (خروجی وسط یه رشته‌ی
            # فارسی بریده می‌شد، یعنی به سقف توکن خورده بود). فضای بیشتر
            # این ریسک رو کمتر می‌کنه، و _recover_truncated_actions هم
            # به‌عنوان fallback برای وقتی که بازم اتفاق بیفته اضافه شده.
            max_tokens=2200,
        )
        raw = response.choices[0].message.content.strip()
        finish_reason = getattr(response.choices[0], "finish_reason", None)
        data = _extract_json_object(raw)
        if data is None:
            # FIX: قبلاً اگه پارس کامل شکست می‌خورد، کل پیام (حتی اگه چندتا
            # اکشن قبلش کامل و سالم بودن) دور ریخته می‌شد. الان قبل از
            # تسلیم شدن، تلاش می‌کنیم اکشن‌های *کامل*ی که تا لحظه‌ی قطع‌شدن
            # نوشته شده بودن رو نجات بدیم.
            recovered = _recover_truncated_actions(raw)
            if recovered:
                print(
                    f"⚠️ smart planner: model output was truncated "
                    f"(finish_reason={finish_reason}, len={len(raw)}) — "
                    f"recovered {len(recovered)} complete action(s) out of what was written so far"
                )
                data = {"actions": recovered}
            else:
                # FIX: قبلاً فقط ۳۰۰ کاراکتر اول لاگ می‌شد که برای تشخیص
                # علت واقعی (قطع‌شدن به خاطر max_tokens، یا واقعاً JSON
                # بدفرم) کافی نبود. الان طول کامل + finish_reason + ۵۰۰
                # کاراکتر لاگ می‌شه.
                print(
                    f"⚠️ smart planner: could not parse JSON from model output "
                    f"(finish_reason={finish_reason}, len={len(raw)}): {raw[:500]!r}"
                )
                return []
=======
            max_tokens=600,
        )
        raw = response.choices[0].message.content.strip()
        if raw.lower() in ("null", "none", ""):
            return []
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
        actions = data.get("actions", [])
        if not isinstance(actions, list):
            return []
    except Exception as e:
        print(f"⚠️ smart planner extract failed: {e}")
        return []

<<<<<<< HEAD
    return _save_smart_planner_actions(user_id, actions, today)


# ── Pending study-block proposals (approval loop) ─────────────────────────────
APPROVAL_KEYWORDS = [
    "تایید", "تأیید", "تاييد", "آره", "اره", "بله", "باشه", "اوکی",
    "اوکیه", "قبوله", "قبول", "قفل کن", "ثبت کن", "حله", "yes", "ok",
]
REJECT_KEYWORDS = ["نه", "لغو", "نمیخوام", "نمی‌خوام", "بیخیال", "بی‌خیال", "ردش", "no"]


def _consume_pending_plan(session, user_id: int, message: str):
    """
    اگه برای کاربر پیشنهاد مطالعه‌ی باز (proposed) وجود داشته باشه و این
    پیام کوتاه تأیید/رد باشه، وضعیتش رو تعیین می‌کنه. خروجی:
        ("approved", items) / ("rejected", None) / (None, None)
    پنجره فقط یک پیامه — مثل reflection، پیام‌های بعدی تفسیر نمی‌شن.
    """
    plan = (
        session.query(PendingPlan)
        .filter(PendingPlan.user_id == user_id, PendingPlan.status == "proposed")
        .order_by(PendingPlan.id.desc())
        .first()
    )
    if not plan:
        return None, None

    text = message.strip().lower()
    if not text or len(text) > 80:
        return None, None

    has_reject = any(kw in text for kw in REJECT_KEYWORDS)
    has_approve = any(kw in text for kw in APPROVAL_KEYWORDS)

    if has_approve and not has_reject:
        try:
            items = json.loads(plan.plan_json)
        except Exception:
            items = []
        if not isinstance(items, list):
            items = []
        plan.status = "applied"
        return "approved", items

    if has_reject:
        plan.status = "discarded"
        return "rejected", None

    return None, None


def _apply_plan_items(session, user_id: int, items: list) -> list:
    """بلوک‌های تأییدشده رو قفل می‌کنه (فقط اسلات‌هایی که هنوز خالی‌ان)."""
    locked = []
    for it in items:
        try:
            d = date_type.fromisoformat(it["date"])
            hour = int(it["hour"])
        except (KeyError, TypeError, ValueError):
            continue
        existing = _day_items(_load_unified_items(session, user_id, d), d.isoformat())
        if _slot_key(d.isoformat(), hour) in existing:
            continue
        text = str(it.get("text", "")).strip()
        if not text:
            continue
        _lock_item(session, user_id, d, hour, text)
        locked.append({
            "type": "study_block", "text": text,
            "date": d.isoformat(), "day": _get_persian_day(d), "hour": hour,
        })
    session.commit()
    return locked


# ── Cognitive Load Spacing (Principle #3) ───────────────────────────────────
HEAVY_DEADLINE_KEYWORDS = [
    "امتحان", "ازمون", "تست", "تحویل", "ددلاین", "پروژه", "ارائه",
    "پایان‌نامه", " پایاننامه", "دفاع", "کوییز", "quiz", "exam", "deadline",
]

# چند هفته‌ی آینده برای weekly_slot تکرارشونده («هر شنبه …») پر بشه
RECURRING_WEEKS = 4

# نشونه‌های «فریز/خستگی بعد از پومودوروهای پشت‌سرهم» در پروفایل روان‌شناختی
LOW_STAMINA_KEYWORDS = ["اهمال", "تعویق", "فریز", "فلج", "شروع نمی", "رها", "خسته", "فرسودگی"]


def _is_heavy_deadline(text: str) -> bool:
    """Returns True if the task text looks like a high-stakes deadline/exam."""
    t = text.lower()
    return any(kw in t for kw in HEAVY_DEADLINE_KEYWORDS)


def _cognitive_stamina(session, user_id: int) -> str:
    """
    پروفایل self-reported کاربر رو می‌سنجه: اگه نشونه‌ی اهمال‌کاری/فریز/
    خستگی سریع داره → 'low' یعنی بلوک‌ها باید کوچیک‌تر و پراکنده‌تر باشن.
    """
    ps = session.query(Psychology).filter_by(user_id=user_id).first()
    if not ps:
        return "normal"
    blob = " ".join([
        " ".join(_json_list(ps.procrastination_patterns)),
        " ".join(_json_list(ps.fear_patterns)),
        " ".join(_json_list(ps.stress_triggers)),
    ])
    return "low" if any(kw in blob for kw in LOW_STAMINA_KEYWORDS) else "normal"


def _propose_study_blocks(
    session, user_id: int, deadline_date: date_type, deadline_text: str, today: date_type
) -> list:
    """
    به‌جای قفل خودکار، بلوک‌های مطالعه‌ی ~۲ پومودورویی (۱.۵-۲ ساعته) رو
    «پیشنهاد» می‌ده تا بعد از تأیید کاربر قفل بشن. قواعد:
      - فقط روزهای بین امروز و موعد (هیچ بلوکی برای گذشته).
      - حداکثر ۱ بلوک ۲ ساعته در روز (جلوگیری از فریز شناختی).
      - پروفایل stamina=low → پنجره‌ی آماده‌سازی طولانی‌تر (تا ۶ روز) با
        بلوک‌های پراکنده؛ پروفایل عادی → تا ۴ روز.
      - همیشه یک بلوک «مرور نهایی» روز قبلِ موعد.
    خروجی: [{"date","hour","text"}, ...] بدون هیچ نوشتنی در دیتابیس.
    """
    if deadline_date <= today:
        return []

    subject = deadline_text
    for kw in HEAVY_DEADLINE_KEYWORDS:
        idx = subject.find(kw)
        if idx != -1:
            subject = subject[idx:].strip()
            break

    stamina = _cognitive_stamina(session, user_id)
    max_days = 6 if stamina == "low" else 4

    days = []
    d = deadline_date - timedelta(days=1)
    while d >= today and len(days) < max_days:
        days.append(d)
        d -= timedelta(days=1)
    days.reverse()

    proposals: list = []
    prep_days = days[:-1] if len(days) > 1 else []
    review_day = days[-1] if days else None

    for i, day in enumerate(prep_days):
        occupied = _occupied_hours(session, user_id, day)
        hour = _first_free_hour(occupied, preferred=16)
        proposals.append({
            "date": day.isoformat(), "hour": hour,
            "text": f"مطالعه گام {i + 1}: {subject}",
        })

    if review_day is not None:
        occupied = _occupied_hours(session, user_id, review_day)
        hour = _first_free_hour(occupied, preferred=10)
        proposals.append({
            "date": review_day.isoformat(), "hour": hour,
            "text": f"مرور نهایی: {subject}",
        })

    return proposals


def _save_smart_planner_actions(user_id: int, actions: list, today: date_type) -> list:
    """
    actionهای استخراج‌شده از چت رو روی مخزن یکپارچه (TaskSlot، یک ردیف به
    ازای هر «YYYY-MM-DD|HH») قفل می‌کنه. Zero Unscheduled Policy: هر آیتم تاریخ و
    ساعت نهایی می‌گیره — ساعت مدل اگه آزاد بود رعایت می‌شه، وگرنه اولین
    اسلات منطقیِ خالی خودکار انتخاب می‌شه.

    موعد سنگین (امتحان/پروژه): به‌جای قفل خودکارِ بلوک‌های آمادگی، یه
    PendingPlan پیشنهادی ثبت می‌شه که توی چت مطرح و منتظر تأیید می‌مونه.
    """
    done = []
    session = get_session()
    try:
        # ضدتکرار درون‌دسته‌ای: مدل گاهی یک کار را دو بار (با متن کمی متفاوت)
        # در همان خروجی استخراج می‌کند — اینجا هم فیلتر می‌شود.
        batch_seen: dict = {}  # (date_iso, fingerprint) -> True
        for action in actions:
            atype = action.get("type")
            text = _normalize_persian(action.get("text", "")).strip()
            if not text:
                continue

            raw_hour = action.get("hour")
            try:
                hour_hint = int(raw_hour) if raw_hour is not None else None
            except (TypeError, ValueError):
                hour_hint = None

            # ── عادت روزانه («هر روز …») → جدول Habit، نه تسک تاریخ‌دار ──
            if atype == "habit":
                fp_habit = _task_fingerprint(text)
                habits = (
                    session.query(Habit)
                    .filter(Habit.user_id == user_id, Habit.is_active == True)
                    .all()
                )
                # FIX: قبلاً فقط تطابق ۱۰۰٪ name جلوی تکرار را می‌گرفت؛
                # الان تشابه معنایی نام عادت هم چک می‌شود.
                existing = next(
                    (h for h in habits if _fingerprints_match(fp_habit, _task_fingerprint(h.name))),
                    None,
                )
                if not existing:
                    session.add(Habit(
                        user_id=user_id,
                        name=text[:200],
                        habit_type="positive",
                        frequency="daily",
                        is_active=True,
                    ))
                    done.append({"type": "habit", "text": text, "hour": hour_hint})
                continue

            # تاریخ دقیق همیشه با کد پایتون حساب می‌شه نه LLM.
            target_date = _resolve_action_date(action, today)
            if target_date is None and action.get("date"):
                try:
                    target_date = date_type.fromisoformat(action["date"])
                except Exception:
                    target_date = None
            if target_date is None:
                target_date = today

            day_name = _get_persian_day(target_date)

            # ── Smart Deduplication ─────────────────────────────────────
            # اگر همین هسته‌ی معنایی قبلاً برای این تاریخ ثبت شده باشد
            # (چه از دفعات قبل در DB، چه در همین دسته‌ی actions)، به‌جای
            # ساخت آیتم جدید همان آیتم آپدیت/نادیده گرفته می‌شود.
            fp_new = _task_fingerprint(text)
            batch_key = (target_date.isoformat(), fp_new)
            updated_existing = False
            if batch_key in batch_seen:
                # تکرار درون همان خروجی مدل — هیچ ننویس
                done.append({
                    "type": "duplicate_skipped", "text": text,
                    "date": target_date.isoformat(), "day": day_name, "hour": hour_hint,
                })
                continue

            assigned_hour, updated_existing = _dedup_upsert_item(
                session, user_id, target_date, hour_hint, text
            )
            batch_seen[batch_key] = True

            if atype == "weekly_slot" and action.get("recurring"):
                # FIX (حفره‌ی تکرار هفتگی): قبلاً weekly_slot فقط توی «یک»
                # هفته ذخیره می‌شد و عملاً هیچ‌وقت واقعاً recurring نبود.
                # الان همون اسلاتِ هم‌روز/هم‌ساعت برای چند هفته‌ی آینده
                # تکثیر می‌شه (در هر هفته اگه ساعت اشغال بود، آزادترین
                # منطقی جایگزین می‌شه) — با ضدتکرار هوشمند برای هر هفته.
                for w in range(1, RECURRING_WEEKS):
                    d = target_date + timedelta(weeks=w)
                    _h_w, _upd_w = _dedup_upsert_item(session, user_id, d, assigned_hour, text)
                done.append({
                    "type": "weekly_recurring", "text": text, "day": day_name,
                    "hour": assigned_hour, "weeks": RECURRING_WEEKS,
                    "updated_existing": updated_existing,
                })
            elif atype == "weekly_slot":
                done.append({
                    "type": "weekly", "text": text, "day": day_name, "hour": assigned_hour,
                    "updated_existing": updated_existing,
                })
            else:
                done.append({
                    "type": "updated" if updated_existing else "daily", "text": text,
                    "date": target_date.isoformat(), "day": day_name, "hour": assigned_hour,
                    "updated_existing": updated_existing,
                })

            # Proactive decomposition — proposal-first، بدون قفل خودکار.
            if atype != "weekly_slot" and _is_heavy_deadline(text):
                open_proposal = (
                    session.query(PendingPlan)
                    .filter(PendingPlan.user_id == user_id, PendingPlan.status == "proposed")
                    .first()
                )
                if not open_proposal:
                    blocks = _propose_study_blocks(session, user_id, target_date, text, today)
                    if blocks:
                        session.add(PendingPlan(
                            user_id=user_id,
                            plan_json=json.dumps(blocks, ensure_ascii=False),
                        ))
                        done.append({"type": "proposal", "blocks": blocks})
=======
    done = []
    session = get_session()
    try:
        for action in actions:
            atype = action.get("type")
            text  = action.get("text", "").strip()
            if not text:
                continue

            if atype == "daily_task":
                date_str = action.get("date", today.isoformat())
                try:
                    target_date = date_type.fromisoformat(date_str)
                except Exception:
                    target_date = today

                state = session.query(DailyState).filter(
                    DailyState.date == target_date.isoformat()
                ).first()
                if not state:
                    state = DailyState(date=target_date.isoformat(), current_tasks=json.dumps([]))
                    session.add(state)
                    session.flush()

                raw_tasks = state.current_tasks
                tasks = json.loads(raw_tasks) if isinstance(raw_tasks, str) else (raw_tasks or [])
                if not any(t.get("text") == text for t in tasks if isinstance(t, dict)):
                    new_id = max((t["id"] for t in tasks if isinstance(t, dict)), default=0) + 1
                    tasks.append({"id": new_id, "text": text, "completed": False})
                    state.current_tasks = json.dumps(tasks, ensure_ascii=False)
                    day_fa = _get_persian_day(target_date)
                    done.append({"type": "daily", "text": text, "date": target_date.isoformat(), "day": day_fa})

            elif atype == "weekly_slot":
                day_name = action.get("day", "")
                hour = int(action.get("hour", 9))
                if day_name not in PERSIAN_DAYS:
                    continue

                today_idx  = PERSIAN_DAYS.index(_get_persian_day(today))
                target_idx = PERSIAN_DAYS.index(day_name)
                diff = target_idx - today_idx
                if diff < 0:
                    diff += 7
                target_date = today + timedelta(days=diff)
                week_key = _get_week_key_for_date(target_date)

                record = session.query(WeeklySchedule).filter(
                    WeeklySchedule.week_key == week_key
                ).first()
                if not record:
                    record = WeeklySchedule(week_key=week_key, schedule_data=json.dumps({}))
                    session.add(record)
                    session.flush()

                raw_sched = record.schedule_data
                schedule = json.loads(raw_sched) if isinstance(raw_sched, str) else (raw_sched or {})
                slot_key = f"{day_name}-{hour}"
                if slot_key not in schedule:
                    schedule[slot_key] = text
                    record.schedule_data = json.dumps(schedule, ensure_ascii=False)
                    done.append({"type": "weekly", "text": text, "day": day_name, "hour": hour})
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9

        session.commit()
    except Exception as e:
        print(f"⚠️ smart planner save failed: {e}")
        session.rollback()
    finally:
        session.close()

    return done


<<<<<<< HEAD
async def _async_smart_planner(user_id: int, user_msg: str, assistant_msg: str) -> list:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_smart_planner, user_id, user_msg, assistant_msg)


@app.post("/api/session/close")
async def close_session(request: SessionCloseRequest, current_user: User = Depends(get_current_user)):
    """
    End-of-Day Closure Protocol:
      1) خلاصه‌ی روز توی ContextSnapshot ذخیره می‌شه (حافظه‌ی اپیزودیک چت بعدی).
      2) آمار تکمیل امروز از مخزن یکپارچه محاسبه می‌شه.
      3) نمای فردا خودش از آیتم‌های تاریخ‌دارِ «فردا» ساخته می‌شه — یعنی
         هیچ state کهنه‌ای برای صفر کردن وجود نداره؛ صبح، DailyView با
         آیتم‌های تاریخ‌دار فردا (یا seed خودکار) شروع می‌شه.
    """
    try:
        mm = MemoryManager(user_id=current_user.id, session_id=PROCESS_SESSION_ID)
        mm.save_context_snapshot(
=======
async def _async_smart_planner(user_msg: str, assistant_msg: str) -> list:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_smart_planner, user_msg, assistant_msg)


@app.post("/api/session/close")
async def close_session(request: SessionCloseRequest):
    try:
        memory_manager.save_context_snapshot(
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
            summary=request.summary,
            active_tasks=request.active_tasks,
            key_decisions=request.key_decisions,
            open_questions=request.open_questions,
            mood_at_end=request.mood_at_end,
            topics_discussed=request.topics_discussed,
        )
<<<<<<< HEAD

        session = get_session()
        try:
            today = _today_iran()
            tomorrow = today + timedelta(days=1)
            day = _day_items(_load_unified_items(session, current_user.id, today), today.isoformat())
            total_tasks = len(day)
            completed_tasks = sum(1 for v in day.values() if v["completed"])
        finally:
            session.close()

        return {
            "status": "success",
            "session_id": PROCESS_SESSION_ID,
            "day_summary": {
                "date": today.isoformat(),
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "open_tasks": total_tasks - completed_tasks,
            },
            "tomorrow_date": tomorrow.isoformat(),
            "fresh_day_prepared": True,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("session close failed")
        raise HTTPException(status_code=500, detail="خطا در بستن سشن. دوباره تلاش کنید.")


@app.post("/api/memory/daily-state")
async def update_daily_state(state: DailyStateUpdate, current_user: User = Depends(get_current_user)):
    try:
        mm = MemoryManager(user_id=current_user.id)
        mm.update_daily_state(
=======
        return {"status": "success", "session_id": SESSION_ID}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/memory/daily-state")
async def update_daily_state(state: DailyStateUpdate):
    try:
        memory_manager.update_daily_state(
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
            mood=state.mood,
            energy=state.energy,
            stress_level=state.stress_level,
            focus_level=state.focus_level,
            sleep_hours=state.sleep_hours,
            sleep_quality=state.sleep_quality,
            current_tasks=state.current_tasks,
            blockers=state.blockers,
            notes=state.notes,
        )
        return {"status": "success", "message": "وضعیت روزانه به‌روزرسانی شد"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memory")
<<<<<<< HEAD
async def get_memory(current_user: User = Depends(get_current_user)):
    mm = MemoryManager(user_id=current_user.id)
    return {
        "persona": mm.get_persona(),
        "psychology": mm.get_psychology(),
        "daily_state": mm.get_today_state(),
        "active_goals": mm.get_active_goals(),
        "recent_events": mm.get_recent_events(limit=10),
        "active_habits": mm.get_active_habits(),
        "last_snapshot": mm.get_last_snapshot(),
=======
async def get_memory():
    return {
        "persona": memory_manager.get_persona(),
        "psychology": memory_manager.get_psychology(),
        "daily_state": memory_manager.get_today_state(),
        "active_goals": memory_manager.get_active_goals(),
        "recent_events": memory_manager.get_recent_events(limit=10),
        "active_habits": memory_manager.get_active_habits(),
        "last_snapshot": memory_manager.get_last_snapshot(),
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    }


@app.get("/api/conversation-history")
<<<<<<< HEAD
async def get_conversation_history(
    limit: int = 100,
    current_user: User = Depends(get_current_user),
):
    """
    FIX: صفحه‌ی چت باید این endpoint رو موقع باز شدن صدا بزنه (قبلاً یه
    پیام خوش‌آمد hardcoded نشون می‌داد و کل تاریخچه گم می‌شد). الان به‌سادگی
    آخرین `limit` پیام (پیش‌فرض ۱۰۰) رو برمی‌گردونه — بدون فیلتر زمانی، چون
    نیازی به منطق پیچیده‌ی «۲۴ ساعت / حداقل چندتا» نبود؛ ۱۰۰ پیام آخر برای
    نشون‌دادن توی UI کافیه. توجه: این جدا از پیامی‌هاییه که به‌عنوان context
    به Gemini فرستاده می‌شه (اونجا فقط ۱۰ تا ۱۵ پیام آخر از طریق
    MAX_HISTORY_FOR_LLM استفاده می‌شه، نه همه‌ی این ۱۰۰ تا — تا هزینه/توکن
    غیرضروری روی هر پیام چت مصرف نشه).
    """
    mm = MemoryManager(user_id=current_user.id)
    return {"history": mm.get_recent_conversations(limit=limit)}


@app.get("/api/memory/belief-revisions")
async def get_belief_revisions(current_user: User = Depends(get_current_user)):
    """
    لایه‌ی ۵ داربست شناختی: تاریخچه‌ی تغییر باورهای self-reported کاربر —
    هر بار که یه سوال بازتابی باعث اصلاح یه باور شده، اینجا ثبته.
    برای یه UI آینده (مثلاً یه تایم‌لاین «چطور خودشناسی‌ت تغییر کرده»).
    """
    mm = MemoryManager(user_id=current_user.id)
    return {"revisions": mm.get_belief_revision_history()}


@app.post("/api/memory/event")
async def add_event(
    event_type: str, title: str, description: str = "",
    current_user: User = Depends(get_current_user),
):
    try:
        mm = MemoryManager(user_id=current_user.id)
        event_id = mm.add_event(
=======
async def get_conversation_history():
    return {"history": memory_manager.get_all_conversations()}


@app.post("/api/memory/event")
async def add_event(event_type: str, title: str, description: str = ""):
    try:
        event_id = memory_manager.add_event(
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
            event_type=event_type,
            title=title,
            description=description,
        )
        return {"status": "success", "event_id": event_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/goals")
async def add_goal(
    title: str,
    description: str = "",
    category: str = "",
    priority: int = 5,
    timeframe: str = "mid",
<<<<<<< HEAD
    current_user: User = Depends(get_current_user),
):
    try:
        mm = MemoryManager(user_id=current_user.id)
        goal_id = mm.add_goal(
=======
):
    try:
        goal_id = memory_manager.add_goal(
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
            title=title,
            description=description,
            category=category,
            priority=priority,
            timeframe=timeframe,
        )
        return {"status": "success", "goal_id": goal_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/goals")
<<<<<<< HEAD
async def get_goals(current_user: User = Depends(get_current_user)):
    mm = MemoryManager(user_id=current_user.id)
    return {"goals": mm.get_active_goals()}
=======
async def get_goals():
    return {"goals": memory_manager.get_active_goals()}
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9


@app.post("/api/habits")
async def add_habit(
    name: str,
    habit_type: str = "positive",
    frequency: str = "daily",
    category: str = "",
<<<<<<< HEAD
    current_user: User = Depends(get_current_user),
):
    try:
        mm = MemoryManager(user_id=current_user.id)
        habit_id = mm.add_habit(
=======
):
    try:
        habit_id = memory_manager.add_habit(
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
            name=name,
            habit_type=habit_type,
            frequency=frequency,
            category=category,
        )
        return {"status": "success", "habit_id": habit_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/habits/{habit_id}/log")
<<<<<<< HEAD
async def log_habit(
    habit_id: int, completed: bool = True, quality: int = None,
    current_user: User = Depends(get_current_user),
):
    try:
        mm = MemoryManager(user_id=current_user.id)
        mm.log_habit(habit_id=habit_id, completed=completed, quality=quality)
=======
async def log_habit(habit_id: int, completed: bool = True, quality: int = None):
    try:
        memory_manager.log_habit(habit_id=habit_id, completed=completed, quality=quality)
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
        return {"status": "success", "message": "عادت ثبت شد"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── DailyView Endpoints ────────────────────────────────────────────────────────

@app.get("/api/daily/tasks")
<<<<<<< HEAD
async def get_daily_tasks(current_user: User = Depends(get_current_user)):
    """
    DailyView = کوئریِ «آیتم‌های امروز» روی مخزن یکپارچه (کلید «YYYY-MM-DD|HH»).
    اگه امروز خالی باشه، تودوهای اولیه (اهداف + عادت‌ها) خودکار قفل می‌شن.
    id هر تسک = ساعتِ اسلاتش (عدد، یکتا در طول روز، پایدار بین رفرش‌ها).
    """
    session = get_session()
    try:
        today_iran = _today_iran()
        today_iso = today_iran.isoformat()
        _seed_today_if_empty(session, current_user.id)
        day = _day_items(_load_unified_items(session, current_user.id, today_iran), today_iso)
        entries = sorted((_parse_slot_key(k)[1], v) for k, v in day.items())
        tasks = [
            {"id": hour, "text": item["text"], "completed": item["completed"]}
            for hour, item in entries
        ]

        # عادت‌های فعال همیشه به لیست امروز اضافه می‌شن (id منفی = habit_id)
        # تا «هر روز پیاده‌روی» بدون نیاز به خالی‌بودن روز دیده بشه.
        slot_texts = {t["text"] for t in tasks}
        habits = (
            session.query(Habit)
            .filter(Habit.user_id == current_user.id, Habit.is_active == True)
            .all()
        )
        for h in habits:
            if h.name in slot_texts:
                continue
            logged_today = (
                session.query(HabitLog)
                .filter(
                    HabitLog.user_id == current_user.id,
                    HabitLog.habit_id == h.id,
                    HabitLog.date == today_iso,
                    HabitLog.completed == True,
                )
                .first()
            )
            tasks.append({
                "id": -h.id, "text": h.name,
                "completed": bool(logged_today), "habit": True,
            })

        state = (
            session.query(DailyState)
            .filter(DailyState.user_id == current_user.id, DailyState.date == today_iso)
            .first()
        )
        return {
            "date": today_iso,
            "tasks": tasks,
            "mood": state.mood if state else None,
            "energy": state.energy if state else None,
            "notes": state.notes if state else None,
=======
async def get_daily_tasks():
    session = get_session()
    try:
        state = _get_or_create_today_state(session)
        tasks = _parse_tasks(state)
        return {
            "date": state.date,
            "tasks": tasks,
            "mood": state.mood,
            "energy": state.energy,
            "notes": state.notes,
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
        }
    finally:
        session.close()


@app.post("/api/daily/tasks")
<<<<<<< HEAD
async def add_daily_task(req: NewTaskRequest, current_user: User = Depends(get_current_user)):
    """تسک سریع: همیشه در مخزن یکپارچه با تاریخ امروز قفل می‌شه — ساعتش
    خودکار اولین اسلات منطقیِ خالیه (Zero Unscheduled Policy)."""
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="متن تسک خالیه")
    session = get_session()
    try:
        today = _today_iran()
        occupied = _occupied_hours(session, current_user.id, today)
        hour = _first_free_hour(occupied)
        _lock_item(session, current_user.id, today, hour, text)
        session.commit()
        return {"status": "success", "task": {"id": hour, "text": text, "completed": False}}
=======
async def add_daily_task(req: NewTaskRequest):
    session = get_session()
    try:
        state = _get_or_create_today_state(session)
        tasks = _parse_tasks(state)
        new_id = max((t["id"] for t in tasks), default=0) + 1
        tasks.append({"id": new_id, "text": req.text, "completed": False})
        _save_tasks(session, state, tasks)
        return {"status": "success", "task": {"id": new_id, "text": req.text, "completed": False}}
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    finally:
        session.close()


@app.patch("/api/daily/tasks/{task_id}")
<<<<<<< HEAD
async def toggle_daily_task(
    task_id: int, req: TaskToggleRequest,
    current_user: User = Depends(get_current_user),
):
    """
    task_id > 0  → ساعت اسلات در مخزن یکپارچه (فلگ completed).
    task_id < 0  → عادت (id = -habit_id): تکمیل امروز با HabitLog ثبت/حذف
                   می‌شه و streak همون منطق MemoryManager به‌روز می‌شه.
    """
    session = get_session()
    try:
        today_iso = _today_str()

        if task_id < 0:
            habit_id = -task_id
            habit = session.get(Habit, habit_id)
            if not habit or habit.user_id != current_user.id:
                raise HTTPException(status_code=404, detail="عادت پیدا نشد")
            logs_today = (
                session.query(HabitLog)
                .filter(
                    HabitLog.user_id == current_user.id,
                    HabitLog.habit_id == habit_id,
                    HabitLog.date == today_iso,
                )
                .all()
            )
            if req.completed and not logs_today:
                session.add(HabitLog(
                    user_id=current_user.id,
                    habit_id=habit_id,
                    date=today_iso,
                    completed=True,
                ))
                habit.streak_current = (habit.streak_current or 0) + 1
                habit.streak_best = max(habit.streak_best or 0, habit.streak_current)
                habit.updated_at = datetime.utcnow()
            elif not req.completed and logs_today:
                for lg in logs_today:
                    session.delete(lg)
                habit.streak_current = max(0, (habit.streak_current or 0) - 1)
                habit.updated_at = datetime.utcnow()
            session.commit()
            return {"status": "success", "task_id": task_id, "completed": req.completed}

        today = _today_iran()
        day = _day_items(_load_unified_items(session, current_user.id, today), today.isoformat())
        target = None
        for key, item in day.items():
            _, hour = _parse_slot_key(key)
            if hour == task_id:
                target = item
                break
        if target is None:
            raise HTTPException(status_code=404, detail="تسک پیدا نشد")
        _lock_item(session, current_user.id, today, task_id, target["text"], completed=req.completed)
        session.commit()
=======
async def toggle_daily_task(task_id: int, req: TaskToggleRequest):
    session = get_session()
    try:
        state = _get_or_create_today_state(session)
        tasks = _parse_tasks(state)
        updated = False
        for task in tasks:
            if task["id"] == task_id:
                task["completed"] = req.completed
                updated = True
                break
        if not updated:
            raise HTTPException(status_code=404, detail="تسک پیدا نشد")
        _save_tasks(session, state, tasks)
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
        return {"status": "success", "task_id": task_id, "completed": req.completed}
    finally:
        session.close()


@app.post("/api/daily/feedback")
<<<<<<< HEAD
async def save_daily_feedback(req: FeedbackRequest, current_user: User = Depends(get_current_user)):
    session = get_session()
    try:
        state = _get_or_create_today_state(session, current_user.id)
        existing = state.notes or ""
        # FIX (bug #4): show the timestamp in Iran local time, not raw
        # server time (Vercel is UTC), so notes don't look off by ~3.5h.
        timestamp = _now_iran().strftime("%H:%M")
=======
async def save_daily_feedback(req: FeedbackRequest):
    session = get_session()
    try:
        state = _get_or_create_today_state(session)
        existing = state.notes or ""
        timestamp = datetime.now().strftime("%H:%M")
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
        separator = "\n---\n" if existing else ""
        state.notes = f"{existing}{separator}[{timestamp}] {req.feedback}"
        session.commit()
        return {"status": "success", "message": "فیدبک ذخیره شد"}
    finally:
        session.close()


# ── WeeklyView Endpoints ───────────────────────────────────────────────────────

@app.get("/api/weekly/schedule")
<<<<<<< HEAD
async def get_weekly_schedule(
    week_offset: int = 0,
    current_user: User = Depends(get_current_user),
):
    """
    WeeklyView = کوئری «آیتم‌های هفته» روی همون مخزن یکپارچه‌ای که DailyView
    می‌خونه. `week_offset` مثل قبل پشتیبانی می‌شه (0=جاری، 1=بعدی، -1=قبلی).
    schedule همیشه با کلیدهای استاندارد «YYYY-MM-DD|HH» برمی‌گرده و مقدار هر
    کلید {"text", "completed"} است؛ ردیف‌های قدیمی («شنبه-10») شفاف تبدیل
    می‌شن. week_start/week_end (شنبه تا جمعه، ISO) هم برای نمایش بازه.
    """
    session = get_session()
    try:
        week_key = _week_key_for_offset(week_offset)
        week_start, week_end = _week_bounds_for_key(week_key)
        # FIX (TaskSlot): قبلاً اینجا باید رکوردهای چندتا bucket هفته‌ی ISO
        # همپوشان رو merge می‌کردیم چون هفته‌ی ایرانی (شنبه–جمعه) یک بلاب
        # ISO رو قطع می‌کرد. حالا TaskSlot به ازای هر تسک یک ردیف با
        # تاریخ دقیقشه — یک کوئری range ساده‌ی روی همون بازه‌ی تاریخ کافیه،
        # هیچ مفهوم «bucket هفته‌ی ISO» یا merge لازم نیست.
        rows = (
            session.query(TaskSlot)
            .filter(
                TaskSlot.user_id == current_user.id,
                TaskSlot.date >= week_start,
                TaskSlot.date <= week_end,
            )
            .all()
        )
        schedule = {_slot_key(r.date, r.hour): {"text": r.text, "completed": bool(r.completed)} for r in rows}
        return {
            "week_key": week_key,
            "week_offset": week_offset,
            "week_start": week_start,
            "week_end": week_end,
            "schedule": schedule,
        }
=======
async def get_weekly_schedule():
    session = get_session()
    try:
        week_key = _current_week_key()
        record = session.query(WeeklySchedule).filter(WeeklySchedule.week_key == week_key).first()
        if not record:
            return {"week_key": week_key, "schedule": {}}
        raw = record.schedule_data
        schedule = json.loads(raw) if isinstance(raw, str) else (raw or {})
        return {"week_key": week_key, "schedule": schedule}
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    finally:
        session.close()


@app.post("/api/weekly/schedule")
<<<<<<< HEAD
async def save_weekly_schedule(
    req: WeeklyScheduleRequest,
    week_offset: int = 0,
    current_user: User = Depends(get_current_user),
):
    """
    ذخیره‌ی کامل گرید از سمت فرانت برای یک هفته‌ی مشخص (replace-all معنایی:
    هرچی برای این بازه‌ی تاریخ می‌فرسته، جایگزین قبلی می‌شه). ورودی
    نرمالایز می‌شه تا فقط آیتم‌های تاریخ‌دار معتبر ({date}|{hour}) ذخیره
    بشن — هیچ کلید شناوری عبور نمی‌کنه.

    FIX (TaskSlot): نسخه‌ی قبلی مجبور بود بلاب هر bucket هفته‌ی ISOِ
    همپوشان رو جدا بخونه، فقط روزهای همین هفته رو داخلش جایگزین کنه، و
    بقیه‌ی روزهای اون bucket (مثلاً دوشنبه‌ی هفته‌ی قبل) رو دست‌نخورده نگه
    داره — چون یک بلاب مشترک بین چند «هفته‌ی نمایشی» بود. با TaskSlot
    (ردیف‌محور) این پیچیدگی از اساس منتفیه: کافیه تمام ردیف‌های این کاربر
    در بازه‌ی [week_start, week_end] حذف بشن و ورودی جدید جایگزینشون بشه —
    توی یک تراکنش، بدون خطر دست‌کاری داده‌ی هفته‌های دیگه.
    """
    session = get_session()
    try:
        week_key = _week_key_for_offset(week_offset)
        week_start, week_end = _week_bounds_for_key(week_key)
        normalized = _normalize_schedule(req.schedule, week_start)
        # فقط تسک‌هایی که واقعاً داخل بازه‌ی همین هفته‌ی نمایشی‌ان ذخیره می‌شن —
        # اگه فرانت به اشتباه تاریخ بیرون از بازه بفرسته، بی‌صدا کنار گذاشته می‌شه.
        normalized = {
            k: v for k, v in normalized.items()
            if week_start <= _parse_slot_key(k)[0] <= week_end
        }

        session.query(TaskSlot).filter(
            TaskSlot.user_id == current_user.id,
            TaskSlot.date >= week_start,
            TaskSlot.date <= week_end,
        ).delete(synchronize_session=False)

        for key, item in normalized.items():
            d_iso, hour = _parse_slot_key(key)
            session.add(TaskSlot(
                user_id=current_user.id, date=d_iso, hour=hour,
                text=item["text"], completed=item["completed"],
            ))

        session.commit()
        return {"status": "success", "week_key": week_key, "week_offset": week_offset}
=======
async def save_weekly_schedule(req: WeeklyScheduleRequest):
    session = get_session()
    try:
        week_key = _current_week_key()
        record = session.query(WeeklySchedule).filter(WeeklySchedule.week_key == week_key).first()
        schedule_json = json.dumps(req.schedule, ensure_ascii=False)
        if record:
            record.schedule_data = schedule_json
        else:
            record = WeeklySchedule(week_key=week_key, schedule_data=schedule_json)
            session.add(record)
        session.commit()
        return {"status": "success", "week_key": week_key}
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    finally:
        session.close()


# ── Work Tasks API ─────────────────────────────────────────────────────────────

@app.post("/api/work-tasks")
<<<<<<< HEAD
async def create_work_task(payload: WorkTaskCreateRequest, current_user: User = Depends(get_current_user)):
    session = get_session()
    try:
        task = WorkTask(
            user_id=current_user.id,
=======
async def create_work_task(payload: WorkTaskCreateRequest):
    session = get_session()
    try:
        task = WorkTask(
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
            title=payload.title,
            description=payload.description,
            due_at=_parse_dt(payload.due_at),
            estimated_pomodoros=payload.estimated_pomodoros,
            completed_pomodoros=0,
            current_progress=0.0,
            difficulty=payload.difficulty,
            cognitive_load=payload.cognitive_load,
            cognitive_intensity=payload.cognitive_intensity,
            mental_fatigue=payload.mental_fatigue,
            focus_requirements=payload.focus_requirements,
            status="pending",
            extra_metadata=payload.extra_metadata or {},  # FIX: renamed field
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return {"ok": True, "task": worktask_to_dict(task)}
    finally:
        session.close()


@app.get("/api/work-tasks")
<<<<<<< HEAD
async def list_work_tasks(current_user: User = Depends(get_current_user)):
    session = get_session()
    try:
        tasks = (
            session.query(WorkTask)
            .filter(WorkTask.user_id == current_user.id)
            .order_by(WorkTask.created_at.desc())
            .all()
        )
=======
async def list_work_tasks():
    session = get_session()
    try:
        tasks = session.query(WorkTask).order_by(WorkTask.created_at.desc()).all()
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
        return {"ok": True, "tasks": [worktask_to_dict(t) for t in tasks]}
    finally:
        session.close()


@app.patch("/api/work-tasks/{task_id}")
<<<<<<< HEAD
async def update_work_task(
    task_id: int, payload: WorkTaskUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    session = get_session()
    try:
        task = session.get(WorkTask, task_id)
        if not task or task.user_id != current_user.id:
=======
async def update_work_task(task_id: int, payload: WorkTaskUpdateRequest):
    session = get_session()
    try:
        task = session.get(WorkTask, task_id)
        if not task:
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
            return {"ok": False, "error": "Task not found"}
        updates = payload.model_dump(exclude_unset=True)
        if "due_at" in updates:
            updates["due_at"] = _parse_dt(updates["due_at"])
        # FIX: map extra_metadata from Pydantic to DB field name
        if "extra_metadata" in updates:
            task.extra_metadata = updates.pop("extra_metadata")
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        session.commit()
        session.refresh(task)
        return {"ok": True, "task": worktask_to_dict(task)}
    finally:
        session.close()


# ── Reminders API ──────────────────────────────────────────────────────────────

@app.post("/api/reminders")
<<<<<<< HEAD
async def create_reminder(payload: ReminderCreateRequest, current_user: User = Depends(get_current_user)):
    session = get_session()
    try:
        reminder = Reminder(
            user_id=current_user.id,
=======
async def create_reminder(payload: ReminderCreateRequest):
    session = get_session()
    try:
        reminder = Reminder(
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
            title=payload.title,
            message=payload.message,
            reminder_at=_parse_dt(payload.reminder_at),  # FIX: correct field name
            reminder_type=payload.reminder_type,
            sent=False,                                    # FIX: correct field name
            priority=payload.priority,
            language=payload.language,
            rtl=payload.rtl,
            avatar_emotion=payload.avatar_emotion,
            extra_metadata=payload.extra_metadata or {},  # FIX: renamed field
        )
        session.add(reminder)
        session.commit()
        session.refresh(reminder)
        return {"ok": True, "reminder": reminder_to_dict(reminder)}
    finally:
        session.close()


@app.get("/api/reminders")
<<<<<<< HEAD
async def list_reminders(current_user: User = Depends(get_current_user)):
    session = get_session()
    try:
        reminders = (
            session.query(Reminder)
            .filter(Reminder.user_id == current_user.id)
            .order_by(Reminder.reminder_at.asc())
            .all()
        )
=======
async def list_reminders():
    session = get_session()
    try:
        reminders = session.query(Reminder).order_by(Reminder.reminder_at.asc()).all()
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
        return {"ok": True, "reminders": [reminder_to_dict(r) for r in reminders]}
    finally:
        session.close()


@app.patch("/api/reminders/{reminder_id}")
<<<<<<< HEAD
async def update_reminder(
    reminder_id: int, payload: ReminderUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    session = get_session()
    try:
        rem = session.get(Reminder, reminder_id)
        if not rem or rem.user_id != current_user.id:
=======
async def update_reminder(reminder_id: int, payload: ReminderUpdateRequest):
    session = get_session()
    try:
        rem = session.get(Reminder, reminder_id)
        if not rem:
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
            return {"ok": False, "error": "Reminder not found"}
        updates = payload.model_dump(exclude_unset=True)
        if "reminder_at" in updates:
            updates["reminder_at"] = _parse_dt(updates["reminder_at"])
        if "extra_metadata" in updates:
            rem.extra_metadata = updates.pop("extra_metadata")
        for key, value in updates.items():
            if hasattr(rem, key):
                setattr(rem, key, value)
        session.commit()
        session.refresh(rem)
        return {"ok": True, "reminder": reminder_to_dict(rem)}
    finally:
        session.close()


# ── Pomodoro Engine API ────────────────────────────────────────────────────────

@app.post("/api/pomodoro/start")
<<<<<<< HEAD
async def start_pomodoro(payload: PomodoroStartRequest, current_user: User = Depends(get_current_user)):
=======
async def start_pomodoro(payload: PomodoroStartRequest):
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    session = get_session()
    try:
        if payload.task_id:
            task = session.get(WorkTask, payload.task_id)
<<<<<<< HEAD
            if not task or task.user_id != current_user.id:
=======
            if not task:
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
                return {"ok": False, "error": "Task not found"}

        now = datetime.now()
        new_session = PomodoroSession(
<<<<<<< HEAD
            user_id=current_user.id,
=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
            task_id=payload.task_id,
            session_type=payload.session_type,
            start_time=now,
            end_time=now + timedelta(minutes=payload.duration_minutes),  # FIX: set end_time on start
            duration_minutes=payload.duration_minutes,
            status="active",
        )
        session.add(new_session)
        session.commit()
        session.refresh(new_session)
        return {"ok": True, "session": pomodoro_to_dict(new_session)}
    finally:
        session.close()


@app.post("/api/pomodoro/stop/{pomodoro_id}")
<<<<<<< HEAD
async def stop_pomodoro(
    pomodoro_id: int, payload: PomodoroStopRequest,
    current_user: User = Depends(get_current_user),
):
    session = get_session()
    try:
        p_session = session.get(PomodoroSession, pomodoro_id)
        if not p_session or p_session.user_id != current_user.id:
=======
async def stop_pomodoro(pomodoro_id: int, payload: PomodoroStopRequest):
    session = get_session()
    try:
        p_session = session.get(PomodoroSession, pomodoro_id)
        if not p_session:
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
            return {"ok": False, "error": "Session not found"}

        p_session.actual_end_time = datetime.now()
        p_session.status = "completed" if payload.completed else "cancelled"

        if payload.completed and p_session.session_type == "focus" and p_session.task_id:
            task = session.get(WorkTask, p_session.task_id)
            if task:
                task.completed_pomodoros += 1
                if task.estimated_pomodoros > 0:
                    task.current_progress = min(
                        100.0,
                        (task.completed_pomodoros / task.estimated_pomodoros) * 100,
                    )
                # FIX: use correct field name mental_fatigue (not mental_fatigue_estimate)
                task.mental_fatigue = min(10.0, task.mental_fatigue + task.difficulty * 0.1)

        session.commit()
        return {"ok": True, "session_id": pomodoro_id, "status": p_session.status}
    finally:
        session.close()


@app.get("/api/pomodoro/active")
<<<<<<< HEAD
async def get_active_pomodoro(current_user: User = Depends(get_current_user)):
    session = get_session()
    try:
        active = session.query(PomodoroSession).filter(
            PomodoroSession.user_id == current_user.id,
            PomodoroSession.status == "active",
        ).first()
=======
async def get_active_pomodoro():
    session = get_session()
    try:
        active = session.query(PomodoroSession).filter(PomodoroSession.status == "active").first()
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
        return {"ok": True, "active_session": pomodoro_to_dict(active) if active else None}
    finally:
        session.close()

# ── Notification Endpoints ─────────────────────────────────────────────────────
<<<<<<< HEAD

@app.get("/api/notifications/pending")
async def get_pending_notifications(current_user: User = Depends(get_current_user)):
=======
# این دو endpoint را به main.py اضافه کن (قبل از if __name__ == "__main__")

@app.get("/api/notifications/pending")
async def get_pending_notifications():
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    """
    فرانت‌اند هر 30 ثانیه این endpoint را poll می‌کنه.
    یادآورهایی که sent=False هستن و زمانشون رسیده برمی‌گرده.
    """
<<<<<<< HEAD
    # FIX (Supabase/serverless migration): Reminder.reminder_at is now
    # timezone-aware (TIMESTAMPTZ), so `now` must be aware too.
    now = datetime.now(timezone.utc)
    session = get_session()
    try:
        pending = session.query(Reminder).filter(
            Reminder.user_id == current_user.id,
=======
    now = datetime.now()
    session = get_session()
    try:
        pending = session.query(Reminder).filter(
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
            Reminder.sent == False,
            Reminder.reminder_at <= now
        ).order_by(Reminder.reminder_at.asc()).all()

        return {
            "ok": True,
            "notifications": [
                {
                    "id": r.id,
                    "title": r.title,
                    "message": r.message,
                    "reminder_type": r.reminder_type,
                    "priority": r.priority,
                    "reminder_at": r.reminder_at.isoformat() if r.reminder_at else None,
                }
                for r in pending
            ]
        }
    finally:
        session.close()


@app.post("/api/notifications/{reminder_id}/dismiss")
<<<<<<< HEAD
async def dismiss_notification(reminder_id: int, current_user: User = Depends(get_current_user)):
=======
async def dismiss_notification(reminder_id: int):
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    """
    فرانت‌اند بعد از نمایش نوتیف این را صدا می‌زنه تا دوباره نیاد.
    """
    session = get_session()
    try:
        r = session.get(Reminder, reminder_id)
<<<<<<< HEAD
        if not r or r.user_id != current_user.id:
            return {"ok": False, "error": "not found"}
        r.sent = True
        r.sent_at = datetime.now(timezone.utc)
=======
        if not r:
            return {"ok": False, "error": "not found"}
        r.sent = True
        r.sent_at = datetime.now()
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
        session.commit()
        return {"ok": True}
    finally:
        session.close()

<<<<<<< HEAD

# ── Cron Endpoint (Vercel Cron) ─────────────────────────────────────────────

def _verify_cron_secret(authorization: Optional[str]) -> None:
    """
    Validates the `Authorization: Bearer <CRON_SECRET>` header sent by
    Vercel Cron (Vercel automatically attaches this header to cron-triggered
    requests when a `CRON_SECRET` environment variable is configured on the
    project). Raises HTTPException on any failure.
    """
    if not CRON_SECRET:
        raise HTTPException(
            status_code=500,
            detail="CRON_SECRET روی سرور تنزیم نشده است.",
        )
    expected = f"Bearer {CRON_SECRET}"
    if not authorization or authorization != expected:
        raise HTTPException(
            status_code=401,
            detail="احراز هویت Cron نامعتبر یا مفقود است.",
        )


@app.get("/api/cron/check-reminders")
async def cron_check_reminders(authorization: Optional[str] = Header(default=None)):
    """
    Called every 10 minutes by Vercel Cron (see the `crons` entry in
    vercel.json). Finds every Reminder whose `reminder_at` has passed and
    that hasn't been notified yet (`sent == False`), dispatches a push
    notification for each (via push_service.dispatch_reminder_notifications),
    and marks them as sent.

    This is the serverless-safe equivalent of
    `scheduler_service._check_and_send_reminders`. On a traditional
    long-running deployment (where the in-process APScheduler is active),
    that scheduler already covers this; on Vercel (where the in-process
    scheduler is skipped at startup, see `startup()` above), this endpoint
    is the only thing that keeps reminders flowing.
    """
    _verify_cron_secret(authorization)

    now = datetime.now(timezone.utc)
    session = get_session()
    processed_ids: list[int] = []
    try:
        due_reminders = (
            session.query(Reminder)
            .filter(Reminder.sent == False, Reminder.reminder_at <= now)
            .order_by(Reminder.reminder_at.asc())
            .all()
        )

        for reminder in due_reminders:
            try:
                dispatch_reminder_notifications(reminder)
            except Exception as e:
                logger.error(f"Push dispatch failed for reminder {reminder.id}: {e}")
            reminder.sent = True
            reminder.sent_at = now
            processed_ids.append(reminder.id)

        session.commit()
    finally:
        session.close()

    logger.info(f"⏰ cron/check-reminders: {len(processed_ids)} reminder(s) processed")
    return {
        "ok": True,
        "checked_at": now.isoformat(),
        "processed_count": len(processed_ids),
        "processed_ids": processed_ids,
    }

=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
