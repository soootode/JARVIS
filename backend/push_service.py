"""
push_service.py - Outbound push-notification dispatch layer
-------------------------------------------------------------
Modular helper/stub functions used by the reminder pipeline (the
`/api/cron/check-reminders` endpoint in main.py, and the in-process
`scheduler_service.py` for non-serverless deployments) to actually notify a
user once a `Reminder` becomes due.

There is currently NO push-subscription storage model in the database (no
table for Web Push subscription objects or FCM device tokens per user), so
`dispatch_reminder_notifications()` is intentionally a no-op beyond logging
until that piece is added. The building blocks below (payload construction,
Web Push dispatch via VAPID, FCM dispatch) are fully implemented and ready to
wire up as soon as subscriptions/device tokens are stored somewhere — see the
docstring on `dispatch_reminder_notifications` for the intended integration
point.
"""

import json
import logging
import os
from typing import Optional

logger = logging.getLogger("PushService")

# ── Web Push (VAPID) config ──────────────────────────────────────────────────
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_CLAIM_EMAIL = os.getenv("VAPID_CLAIM_EMAIL", "mailto:admin@example.com")

# ── FCM (Firebase Cloud Messaging - legacy HTTP API) config ────────────────
# NOTE: Google's legacy HTTP API (`fcm.googleapis.com/fcm/send`) is used here
# for simplicity (single server-key header, no OAuth). If/when this project
# migrates to the newer FCM v1 HTTP API, swap this for a service-account
# based OAuth2 bearer token instead of FCM_SERVER_KEY.
FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY")


def build_reminder_payload(reminder) -> dict:
    """Builds a provider-agnostic notification payload from a Reminder row."""
    return {
        "title": reminder.title,
        "body": reminder.message,
        "data": {
            "reminder_id": reminder.id,
            "reminder_type": reminder.reminder_type,
            "priority": reminder.priority,
        },
    }


def send_web_push(subscription_info: dict, payload: dict) -> bool:
    """
    Sends a single Web Push notification via VAPID.

    `subscription_info` must be the JSON object returned by the browser's
    `PushSubscription.toJSON()` (endpoint + keys.p256dh + keys.auth).
    Returns True on success, False otherwise (including when Web Push isn't
    configured or the `pywebpush` package isn't installed — both are treated
    as a soft no-op rather than an error, since push delivery is best-effort).
    """
    if not (VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY):
        logger.info("Web Push skipped (VAPID keys not configured): %s", payload.get("title"))
        return False

    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        logger.warning("pywebpush is not installed; skipping Web Push dispatch.")
        return False

    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_CLAIM_EMAIL},
        )
        return True
    except WebPushException as e:
        logger.error("Web Push dispatch failed: %s", e)
        return False
    except Exception as e:
        logger.error("Unexpected error during Web Push dispatch: %s", e)
        return False


def send_fcm_push(device_token: str, payload: dict) -> bool:
    """
    Sends a single push notification to an Android/iOS device via FCM's
    legacy HTTP API. Returns True on success, False otherwise (including
    when FCM isn't configured — treated as a soft no-op).
    """
    if not FCM_SERVER_KEY:
        logger.info("FCM push skipped (FCM_SERVER_KEY not configured): %s", payload.get("title"))
        return False

    try:
        import httpx
    except ImportError:
        logger.warning("httpx is not installed; skipping FCM dispatch.")
        return False

    try:
        response = httpx.post(
            "https://fcm.googleapis.com/fcm/send",
            headers={
                "Authorization": f"key={FCM_SERVER_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "to": device_token,
                "notification": {
                    "title": payload.get("title"),
                    "body": payload.get("body"),
                },
                "data": payload.get("data", {}),
            },
            timeout=10.0,
        )
        if response.status_code == 200:
            return True
        logger.error("FCM dispatch failed (%s): %s", response.status_code, response.text)
        return False
    except Exception as e:
        logger.error("Unexpected error during FCM dispatch: %s", e)
        return False


def dispatch_reminder_notifications(reminder) -> None:
    """
    Central dispatch point called once per due `Reminder` row by both the
    Vercel Cron endpoint (`GET /api/cron/check-reminders` in main.py) and the
    in-process scheduler (`scheduler_service.py`, for non-serverless
    deployments).

    There is no push-subscription storage yet, so this currently only logs
    the notification. Once a subscription/device-token table exists (e.g. a
    `PushSubscription` model keyed by `user_id`), wire it up here, for
    example:

        from database import get_session, PushSubscription
        session = get_session()
        try:
            subs = session.query(PushSubscription).filter(
                PushSubscription.user_id == reminder.user_id
            ).all()
        finally:
            session.close()

        payload = build_reminder_payload(reminder)
        for sub in subs:
            if sub.platform == "web":
                send_web_push(sub.subscription_info, payload)
            elif sub.platform in ("android", "ios"):
                send_fcm_push(sub.device_token, payload)
    """
    payload = build_reminder_payload(reminder)
    logger.info("🔔 Reminder due (dispatch stub, no subscriptions wired up yet): %s", payload)
