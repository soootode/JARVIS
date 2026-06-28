"""
main.py - Jarvis-You Backend
Milestone 2: SQLAlchemy + Context Snapshots + Session Management
+ DailyView / WeeklyView endpoints
+ Morning Initialization Protocol
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
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler

from memory_manager import MemoryManager
from memory_updater import extract_memory_updates
from scheduler_service import SchedulerService
from database import (
    get_session, init_db,
    DailyState, EventTask, Habit, Goal, WeeklySchedule,
    WorkTask, Reminder, PomodoroSession,
)

load_dotenv()

scheduler = None
scheduler_service = None

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

# ── App setup ──────────────────────────────────────────────────────────────────

app = FastAPI(title="Jarvis-You Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        # بعد از دیپلوی لیارا، آدرس فرانت‌اند را اینجا اضافه کن:
        # "https://jarvis-frontend.liara.run",
        # "https://yourdomain.ir",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSION_ID = str(uuid.uuid4())
memory_manager = MemoryManager(session_id=SESSION_ID)

# ── Startup: ساخت جداول دیتابیس ───────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    global scheduler, scheduler_service

    init_db()
    print("✅ Database tables ready")

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
PERSONA_JSON = load_json("persona.json")


def build_system_prompt() -> str:
    prompt = SYSTEM_PROMPT_BASE
    if PERSONA_JSON:
        prompt += (
            "\n\n---\nPROFILE DATA (اطلاعات شخصی کاربر - JSON):\n"
            + json.dumps(PERSONA_JSON, ensure_ascii=False, indent=2)
        )
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


class PomodoroStartRequest(BaseModel):
    task_id: int | None = None
    duration_minutes: int = 25
    session_type: str = "focus"  # focus, short_break, long_break


class PomodoroStopRequest(BaseModel):
    completed: bool = True


# ── Helper: parse datetime string ─────────────────────────────────────────────

def _parse_dt(dt_str: str | None):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
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
        session.add(state)
        session.commit()
        session.refresh(state)
    return state


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
    session.commit()


def _dt_iso(x):
    return x.isoformat() if x else None


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

async def _morning_init_if_needed() -> bool:
    """
    بررسی می‌کند آیا DailyState امروز وجود دارد یا خیر.
    اگر نه، تودوهای شخصی‌سازی‌شده از طریق GapGPT می‌سازد.
    True برمی‌گرداند اگر اولین تعامل روز بود.
    """
    session = get_session()
    try:
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

    except Exception as e:
        print(f"⚠️ morning init failed: {e}")
        return False
    finally:
        session.close()


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    persona = memory_manager.get_persona()
    return {
        "status": "running",
        "assistant": "Jarvis-You",
        "user": persona.get("preferred_name", "کاربر"),
        "session_id": SESSION_ID,
        "llm": MODEL,
    }


@app.post("/api/chat", response_model=ChatResponse)
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

            system_prompt += (
                f"\n\n---\nMORNING INIT: امروز اولین تعامل روز است. "
                f"تودوهای زیر برای کاربر تولید شده‌اند: {tasks_preview}. "
                "یک خوش‌آمدگویی صبحگاهی گرم، شخصی و انگیزه‌بخش بده. "
                "به طور خاص به اهداف و برنامه‌های امروز اشاره کن. "
                "پیام کوتاه، صمیمی و محرک باشد."
            )

        history = memory_manager.get_conversation_history()
        messages = build_chat_history(history)
        messages.append({"role": "user", "content": request.message})

        loop = asyncio.get_event_loop()
        assistant_message = await loop.run_in_executor(
            None,
            lambda: _call_llm(system_prompt, messages, temperature=0.7, max_tokens=1500),
        )

        memory_manager.add_conversation(request.message, assistant_message)
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

    except Exception as e:
        print(f"🔥 ارور بک‌اند: {e}")
        raise HTTPException(status_code=500, detail=f"خطا در پردازش: {str(e)}")


async def _async_memory_update(user_msg: str, assistant_msg: str):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _sync_memory_update, user_msg, assistant_msg)


def _sync_memory_update(user_msg: str, assistant_msg: str):
    try:
        updates = extract_memory_updates(
            client=client,
            user_message=user_msg,
            assistant_message=assistant_msg,
            current_memory=memory_manager.memory,
        )
        if updates:
            memory_manager.update_memory_fields(updates)
            print(f"✅ memory updated: {list(updates.keys())}")
    except Exception as e:
        print(f"⚠️ memory update failed (non-critical): {e}")


# ── Smart Planner: استخراج task/deadline از چت ────────────────────────────────

PLANNER_EXTRACT_PROMPT = """
تو یک سیستم استخراج برنامه‌ریزی هستی.
امروز: {today} ({today_fa})
روزهای هفته به فارسی: شنبه، یکشنبه، دوشنبه، سه‌شنبه، چهارشنبه، پنجشنبه، جمعه

از این مکالمه، task یا deadline استخراج کن:
کاربر: {user_message}
دستیار: {assistant_message}

اگر هیچ task یا deadline‌ای نیست: فقط بنویس null

اگر هست، JSON زیر را برگردان:
{{
  "actions": [
    {{
      "type": "daily_task",
      "date": "YYYY-MM-DD",
      "text": "متن تسک به فارسی"
    }},
    {{
      "type": "weekly_slot",
      "day": "شنبه",
      "hour": 14,
      "text": "متن برنامه به فارسی"
    }}
  ]
}}

قوانین:
- برای deadline (مثلاً «شنبه تکلیف شبکه دارم»): یک daily_task برای روز قبل از deadline بساز با متن «مرور و آماده‌سازی: [موضوع]» و یک weekly_slot برای روز deadline با ساعت مناسب
- برای task امروز یا فردا: فقط daily_task
- برای برنامه هفتگی خاص: فقط weekly_slot
- hour باید عدد صحیح بین 7 تا 23 باشد
- date باید از امروز به بعد باشد
- فقط JSON خالص یا null، بدون توضیح
"""

PERSIAN_DAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]


def _get_persian_day(d: date_type) -> str:
    wd = d.weekday()  # Mon=0..Sun=6
    mapping = {5: 0, 6: 1, 0: 2, 1: 3, 2: 4, 3: 5, 4: 6}  # Sat=شنبه
    return PERSIAN_DAYS[mapping[wd]]


def _get_week_key_for_date(d: date_type) -> str:
    return f"{d.year}-W{d.isocalendar()[1]:02d}"


def _sync_smart_planner(user_msg: str, assistant_msg: str) -> list:
    today = date_type.today()
    today_fa = _get_persian_day(today)

    prompt = PLANNER_EXTRACT_PROMPT.format(
        today=today.isoformat(),
        today_fa=today_fa,
        user_message=user_msg,
        assistant_message=assistant_msg[:400],
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "فقط JSON خالص یا null برمی‌گردانی."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=600,
        )
        raw = response.choices[0].message.content.strip()
        if raw.lower() in ("null", "none", ""):
            return []
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        actions = data.get("actions", [])
        if not isinstance(actions, list):
            return []
    except Exception as e:
        print(f"⚠️ smart planner extract failed: {e}")
        return []

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

        session.commit()
    except Exception as e:
        print(f"⚠️ smart planner save failed: {e}")
        session.rollback()
    finally:
        session.close()

    return done


async def _async_smart_planner(user_msg: str, assistant_msg: str) -> list:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_smart_planner, user_msg, assistant_msg)


@app.post("/api/session/close")
async def close_session(request: SessionCloseRequest):
    try:
        memory_manager.save_context_snapshot(
            summary=request.summary,
            active_tasks=request.active_tasks,
            key_decisions=request.key_decisions,
            open_questions=request.open_questions,
            mood_at_end=request.mood_at_end,
            topics_discussed=request.topics_discussed,
        )
        return {"status": "success", "session_id": SESSION_ID}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/memory/daily-state")
async def update_daily_state(state: DailyStateUpdate):
    try:
        memory_manager.update_daily_state(
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
async def get_memory():
    return {
        "persona": memory_manager.get_persona(),
        "psychology": memory_manager.get_psychology(),
        "daily_state": memory_manager.get_today_state(),
        "active_goals": memory_manager.get_active_goals(),
        "recent_events": memory_manager.get_recent_events(limit=10),
        "active_habits": memory_manager.get_active_habits(),
        "last_snapshot": memory_manager.get_last_snapshot(),
    }


@app.get("/api/conversation-history")
async def get_conversation_history():
    return {"history": memory_manager.get_all_conversations()}


@app.post("/api/memory/event")
async def add_event(event_type: str, title: str, description: str = ""):
    try:
        event_id = memory_manager.add_event(
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
):
    try:
        goal_id = memory_manager.add_goal(
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
async def get_goals():
    return {"goals": memory_manager.get_active_goals()}


@app.post("/api/habits")
async def add_habit(
    name: str,
    habit_type: str = "positive",
    frequency: str = "daily",
    category: str = "",
):
    try:
        habit_id = memory_manager.add_habit(
            name=name,
            habit_type=habit_type,
            frequency=frequency,
            category=category,
        )
        return {"status": "success", "habit_id": habit_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/habits/{habit_id}/log")
async def log_habit(habit_id: int, completed: bool = True, quality: int = None):
    try:
        memory_manager.log_habit(habit_id=habit_id, completed=completed, quality=quality)
        return {"status": "success", "message": "عادت ثبت شد"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── DailyView Endpoints ────────────────────────────────────────────────────────

@app.get("/api/daily/tasks")
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
        }
    finally:
        session.close()


@app.post("/api/daily/tasks")
async def add_daily_task(req: NewTaskRequest):
    session = get_session()
    try:
        state = _get_or_create_today_state(session)
        tasks = _parse_tasks(state)
        new_id = max((t["id"] for t in tasks), default=0) + 1
        tasks.append({"id": new_id, "text": req.text, "completed": False})
        _save_tasks(session, state, tasks)
        return {"status": "success", "task": {"id": new_id, "text": req.text, "completed": False}}
    finally:
        session.close()


@app.patch("/api/daily/tasks/{task_id}")
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
        return {"status": "success", "task_id": task_id, "completed": req.completed}
    finally:
        session.close()


@app.post("/api/daily/feedback")
async def save_daily_feedback(req: FeedbackRequest):
    session = get_session()
    try:
        state = _get_or_create_today_state(session)
        existing = state.notes or ""
        timestamp = datetime.now().strftime("%H:%M")
        separator = "\n---\n" if existing else ""
        state.notes = f"{existing}{separator}[{timestamp}] {req.feedback}"
        session.commit()
        return {"status": "success", "message": "فیدبک ذخیره شد"}
    finally:
        session.close()


# ── WeeklyView Endpoints ───────────────────────────────────────────────────────

@app.get("/api/weekly/schedule")
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
    finally:
        session.close()


@app.post("/api/weekly/schedule")
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
    finally:
        session.close()


# ── Work Tasks API ─────────────────────────────────────────────────────────────

@app.post("/api/work-tasks")
async def create_work_task(payload: WorkTaskCreateRequest):
    session = get_session()
    try:
        task = WorkTask(
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
async def list_work_tasks():
    session = get_session()
    try:
        tasks = session.query(WorkTask).order_by(WorkTask.created_at.desc()).all()
        return {"ok": True, "tasks": [worktask_to_dict(t) for t in tasks]}
    finally:
        session.close()


@app.patch("/api/work-tasks/{task_id}")
async def update_work_task(task_id: int, payload: WorkTaskUpdateRequest):
    session = get_session()
    try:
        task = session.get(WorkTask, task_id)
        if not task:
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
async def create_reminder(payload: ReminderCreateRequest):
    session = get_session()
    try:
        reminder = Reminder(
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
async def list_reminders():
    session = get_session()
    try:
        reminders = session.query(Reminder).order_by(Reminder.reminder_at.asc()).all()
        return {"ok": True, "reminders": [reminder_to_dict(r) for r in reminders]}
    finally:
        session.close()


@app.patch("/api/reminders/{reminder_id}")
async def update_reminder(reminder_id: int, payload: ReminderUpdateRequest):
    session = get_session()
    try:
        rem = session.get(Reminder, reminder_id)
        if not rem:
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
async def start_pomodoro(payload: PomodoroStartRequest):
    session = get_session()
    try:
        if payload.task_id:
            task = session.get(WorkTask, payload.task_id)
            if not task:
                return {"ok": False, "error": "Task not found"}

        now = datetime.now()
        new_session = PomodoroSession(
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
async def stop_pomodoro(pomodoro_id: int, payload: PomodoroStopRequest):
    session = get_session()
    try:
        p_session = session.get(PomodoroSession, pomodoro_id)
        if not p_session:
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
async def get_active_pomodoro():
    session = get_session()
    try:
        active = session.query(PomodoroSession).filter(PomodoroSession.status == "active").first()
        return {"ok": True, "active_session": pomodoro_to_dict(active) if active else None}
    finally:
        session.close()

# ── Notification Endpoints ─────────────────────────────────────────────────────
# این دو endpoint را به main.py اضافه کن (قبل از if __name__ == "__main__")

@app.get("/api/notifications/pending")
async def get_pending_notifications():
    """
    فرانت‌اند هر 30 ثانیه این endpoint را poll می‌کنه.
    یادآورهایی که sent=False هستن و زمانشون رسیده برمی‌گرده.
    """
    now = datetime.now()
    session = get_session()
    try:
        pending = session.query(Reminder).filter(
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
async def dismiss_notification(reminder_id: int):
    """
    فرانت‌اند بعد از نمایش نوتیف این را صدا می‌زنه تا دوباره نیاد.
    """
    session = get_session()
    try:
        r = session.get(Reminder, reminder_id)
        if not r:
            return {"ok": False, "error": "not found"}
        r.sent = True
        r.sent_at = datetime.now()
        session.commit()
        return {"ok": True}
    finally:
        session.close()

# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
