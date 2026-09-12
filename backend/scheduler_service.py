import logging
import os
from datetime import datetime, timezone
from database import get_session, Reminder, PomodoroSession, WorkTask, User
from memory_manager import MemoryManager
from push_service import dispatch_reminder_notifications

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SchedulerService")

# ── LLM client برای تشخیص reflection ─────────────────────────────────────────
# جدا از main.py ساخته می‌شه (نه import شده) تا وابستگی دوری بین این دو فایل
# پیش نیاد. اگه GOOGLE_API_KEY نباشه، client خالی می‌مونه و
# check_and_generate_reflection خودش fallback می‌کنه به قوانین دستی.
# این client از طریق Gemini API رسمی گوگل، از طریق endpoint سازگار با OpenAI
# وصل می‌شه (تا کد فراخوانی client.chat.completions.create در همه جا
# بدون تغییر بماند).
_llm_client = None
try:
    from openai import OpenAI
    _google_api_key = os.getenv("GOOGLE_API_KEY")
    if _google_api_key:
        _llm_client = OpenAI(
            api_key=_google_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
except Exception as e:
    logger.warning(f"LLM client برای reflection راه‌اندازی نشد (fallback به قوانین دستی): {e}")


class SchedulerService:
    def __init__(self):
        self.logger = logger

    def run_all(self):
        """متد اصلی که باید به صورت دوره‌ای صدا شود."""
        session = get_session()
        try:
            self._check_and_send_reminders(session)
            self._manage_pomodoro_sessions(session)
            session.commit()
        except Exception as e:
            self.logger.error(f"خطا در اجرای سرویس زمان‌بندی: {e}")
            session.rollback()
        finally:
            session.close()

        # جدا از تراکنش بالا اجرا می‌شه چون MemoryManager خودش session باز
        # می‌کنه؛ خطای یک کاربر نباید بقیه رو متوقف کنه.
        # این job هر ۶۰ ثانیه صدا زده می‌شه (چون run_all برای یادآورها هر
        # دقیقه اجرا می‌شه)، ولی چون reflection خودش gate هفتگی داره، نیازی
        # نیست هر دقیقه چک بشه — فقط سر هر ساعت (minute == 0) اجرا می‌شه تا
        # overhead غیرضروری (باز کردن MemoryManager برای هر کاربر هر دقیقه)
        # نداشته باشیم.
        if datetime.utcnow().minute == 0:
            self._check_behavioral_reflections()

    def _check_behavioral_reflections(self):
        """
        هر tick اسکجولر، برای هر کاربر فعال چک می‌کنه که آیا وقتشه رفتار
        عینی‌شو در برابر پروفایل روان‌شناختی self-reported بسنجه یا نه.
        خود MemoryManager.check_and_generate_reflection داخلی gate داره
        (حداقل ۷ روز بین چک‌ها)، پس صدا زدنش هر بار بی‌خطره — بیشتر وقت‌ها
        فقط یه no-op سریعه.
        """
        session = get_session()
        try:
            user_ids = [u.id for u in session.query(User.id).filter(User.is_active == True).all()]
        finally:
            session.close()

        for user_id in user_ids:
            try:
                mm = MemoryManager(user_id=user_id)
                reflection = mm.check_and_generate_reflection(llm_client=_llm_client)
                if reflection:
                    self.logger.info(f"🪞 reflection generated for user {user_id}: {reflection[:60]}...")
            except Exception as e:
                self.logger.error(f"خطا در بررسی reflection برای کاربر {user_id}: {e}")

    def _check_and_send_reminders(self, session):
        """بررسی و ارسال یادآورهای زمان‌رسیده."""
        # FIX (Supabase/serverless migration): Reminder.reminder_at is now a
        # timezone-aware column (TIMESTAMPTZ on Postgres), so `now` must be
        # tz-aware too — otherwise SQLAlchemy/psycopg would compare an aware
        # column against a naive parameter.
        now = datetime.now(timezone.utc)
        # FIX: field renamed from is_sent → sent, and remind_at → reminder_at
        reminders = session.query(Reminder).filter(
            Reminder.sent == False,
            Reminder.reminder_at <= now
        ).all()

        for reminder in reminders:
            self.logger.info(f"ارسال یادآور: {reminder.title}")
            try:
                dispatch_reminder_notifications(reminder)
            except Exception as e:
                self.logger.error(f"ارسال پوش‌نوتیفیکیشن برای یادآور {reminder.id} شکست خورد: {e}")
            # FIX: field renamed from is_sent → sent
            reminder.sent = True
            reminder.sent_at = now

        if reminders:
            self.logger.info(f"{len(reminders)} یادآور پردازش شد.")

    def _manage_pomodoro_sessions(self, session):
        """مدیریت وضعیت پومودوروها."""
        now = datetime.utcnow()
        # بررسی سشن‌های فعال که زمانشان تمام شده
        active_sessions = session.query(PomodoroSession).filter(
            PomodoroSession.status == "active",
            PomodoroSession.end_time <= now
        ).all()

        for session_item in active_sessions:
            self.logger.info(f"پایان سشن پومودورو: {session_item.id}")
            session_item.status = "completed"
            session_item.actual_end_time = now

            # آپدیت تسک مربوطه اگر وجود داشته باشد
            if session_item.task_id:
                task = session.query(WorkTask).filter(WorkTask.id == session_item.task_id).first()
                if task:
                    task.completed_pomodoros += 1
                    if task.estimated_pomodoros > 0:
                        task.current_progress = min(
                            100.0,
                            (task.completed_pomodoros / task.estimated_pomodoros) * 100
                        )

        if active_sessions:
            self.logger.info(f"{len(active_sessions)} سشن پومودورو تکمیل شد.")
