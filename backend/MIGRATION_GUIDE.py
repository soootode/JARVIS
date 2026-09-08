# ══════════════════════════════════════════════════════
# راهنمای به‌روزرسانی main.py و requirements.txt
# ══════════════════════════════════════════════════════


# ── ۱. requirements.txt ────────────────────────────────
# پکیج‌های جدید را اضافه کن:

"""
fastapi
uvicorn[standard]
python-dotenv
google-genai
pydantic

# جدید:
sqlalchemy>=2.0.0
# برای PostgreSQL (لیارا) - در لوکال نیازی نیست:
# psycopg2-binary>=2.9.0
"""


# ── ۲. تغییرات main.py ────────────────────────────────

# الف) MemoryManager را با session_id مقداردهی کن:
#
# قدیم:
#   memory_manager = MemoryManager()
#
# جدید:
#   import uuid
#   SESSION_ID = str(uuid.uuid4())   # یک بار در startup
#   memory_manager = MemoryManager(session_id=SESSION_ID)


# ب) endpoint چت - snapshot را در پایان سشن ذخیره کن.
# یک endpoint جدید اضافه کن:

"""
@app.post("/api/session/close")
async def close_session(summary: str, active_tasks: list[str] = []):
    \"\"\"در پایان گفتگو فراخوانی می‌شود تا snapshot ذخیره شود.\"\"\"
    memory_manager.save_context_snapshot(
        summary=summary,
        active_tasks=active_tasks,
    )
    return {"status": "snapshot saved", "session_id": memory_manager.session_id}
"""


# ج) endpoint /api/memory را به‌روز کن:
#
# قدیم:
#   return memory_manager.memory
#
# جدید (اختیاری - جزئیات بیشتر):
"""
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
"""


# ── ۳. فایل .env ──────────────────────────────────────

"""
GOOGLE_API_KEY=your_key_here

# لوکال (SQLite):
DATABASE_URL=sqlite:///./jarvis.db

# لیارا (PostgreSQL) - فقط این خط را عوض کن:
# DATABASE_URL=postgresql://user:pass@host:port/dbname

# اختیاری - نمایش SQL queries در ترمینال:
DB_ECHO=false
"""


# ── ۴. نکته مهم: Context Window مدیریت ───────────────
#
# با این معماری، در ابتدای هر چت جدید:
#   1. get_last_snapshot()  →  خلاصه سشن قبل
#   2. get_conversation_history(limit=20)  →  آخرین پیام‌ها
#
# به جای لود کردن کل تاریخچه، فقط snapshot + آخرین N پیام
# به Gemini ارسال می‌شود → کاهش مصرف token و سرعت بیشتر.
#
# منطق get_context_for_llm() این را به صورت خودکار هندل می‌کند.
