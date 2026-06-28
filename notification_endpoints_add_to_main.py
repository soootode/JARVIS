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
