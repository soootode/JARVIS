import logging
from datetime import datetime
from database import get_session, Reminder, PomodoroSession, WorkTask

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SchedulerService")


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

    def _check_and_send_reminders(self, session):
        """بررسی و ارسال یادآورهای زمان‌رسیده."""
        now = datetime.utcnow()
        # FIX: field renamed from is_sent → sent, and remind_at → reminder_at
        reminders = session.query(Reminder).filter(
            Reminder.sent == False,
            Reminder.reminder_at <= now
        ).all()

        for reminder in reminders:
            self.logger.info(f"ارسال یادآور: {reminder.title}")
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
