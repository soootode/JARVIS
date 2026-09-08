"""
email_service.py - Email dispatch via Resend (with safe dev fallback)
---------------------------------------------------------------------
از SDK رسمی Resend برای ارسال ایمیل استفاده می‌کند. اگر RESEND_API_KEY در
env ست نشده باشد (محیط توسعه)، ایمیل به‌جای ارسال واقعی در کنسول لاگ می‌شود
تا هیچ سرویس خارجی یا کلیدی لازم نباشد.

Env vars:
    RESEND_API_KEY   — کلید API رزند (نبودش = حالت توسعه/لاگ)
    EMAIL_FROM       — فرستنده، مثل "Jarvis <noreply@yourdomain.com>"
                       (پیش‌فرض تست: onboarding@resend.dev)
    FRONTEND_URL     — آدرس فرانت برای ساخت لینک‌های ریست/تأیید
"""

import os

try:
    import resend
except ModuleNotFoundError:
    # بسته‌ی resend نصب نباشد، کل بک‌اند بالا نیاید — فقط حالت dev فعال می‌ماند
    resend = None


def is_email_configured() -> bool:
    return bool(os.getenv("RESEND_API_KEY")) and resend is not None


def _dev_log(to: str, subject: str, html: str) -> None:
    print(
        "\n" + "=" * 70 +
        f"\n📧 [DEV MODE - email not sent, RESEND_API_KEY not set]\n"
        f"To     : {to}\n"
        f"Subject: {subject}\n"
        + "-" * 70 +
        f"\n{html}\n" +
        "=" * 70 + "\n"
    )


def send_email(to_email: str, subject: str, html: str) -> bool:
    """
    ارسال ایمیل با Resend. True یعنی ارسال شد (یا در حالت توسعه لاگ شد).
    هیچ exception ای به بالا نشت نمی‌کند — شکست ایمیل نباید جریان auth را بشکند.
    """
    if not to_email:
        return False

    if not is_email_configured():
        _dev_log(to_email, subject, html)
        return True

    resend.api_key = os.getenv("RESEND_API_KEY")
    from_addr = os.getenv("EMAIL_FROM") or "onboarding@resend.dev"

    try:
        params: resend.Emails.SendParams = {
            "from": from_addr,
            "to": [to_email],
            "subject": subject,
            "html": html,
        }
        email = resend.Emails.send(params)
        email_id = email.get("id") if isinstance(email, dict) else getattr(email, "id", "?")
        print(f"📧 email_service: sent to {to_email} (id={email_id})")
        return True
    except Exception as e:
        print(f"⚠️ email_service: send failed to {to_email}: {e}")
        return False


# ── Template helpers ─────────────────────────────────────────────────────────

def _wrap_html(title_fa: str, body_fa: str, cta_text: str, cta_url: str) -> str:
    """قالب تمیز و ریسپانسیو (dark, RTL) برای ایمیل‌های سیستمی."""
    return f"""<!DOCTYPE html>
<html dir="rtl" lang="fa">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  </head>
  <body style="margin:0;padding:0;background:#09090b;font-family:Tahoma,Arial,sans-serif;">
    <div style="max-width:480px;margin:40px auto;background:#18181b;border-radius:12px;
                border:1px solid #3f3f46;overflow:hidden;">
      <div style="padding:28px;text-align:center;border-bottom:1px solid #27272a;">
        <h1 style="color:#fafafa;font-size:20px;margin:0;">جارویس</h1>
      </div>
      <div style="padding:28px;color:#d4d4d8;font-size:14px;line-height:2;">
        <p style="margin:0 0 16px;font-weight:bold;color:#fafafa;">{title_fa}</p>
        <p style="margin:0 0 24px;">{body_fa}</p>
        <div style="text-align:center;">
          <a href="{cta_url}"
             style="display:inline-block;background:#ffffff;color:#000000;
                    text-decoration:none;padding:12px 32px;border-radius:8px;
                    font-weight:bold;font-size:14px;">
            {cta_text}
          </a>
        </div>
        <p style="margin:24px 0 8px;font-size:11px;color:#71717a;">اگر دکمه کار نکرد، این لینک را در مرورگر باز کنید:</p>
        <p style="margin:0 0 16px;font-size:11px;word-break:break-all;">
          <a href="{cta_url}" style="color:#a1a1aa;">{cta_url}</a>
        </p>
        <p style="margin:0;font-size:11px;color:#71717a;">
          اگر شما این درخواست را نداده‌اید، این ایمیل را نادیده بگیرید.
          این لینک بعد از یک ساعت منقضی می‌شود.
        </p>
      </div>
    </div>
  </body>
</html>"""


def send_password_reset_email(to_email: str, reset_link: str) -> bool:
    return send_email(
        to_email=to_email,
        subject="بازیابی رمز عبور جارویس",
        html=_wrap_html(
            title_fa="بازیابی رمز عبور",
            body_fa=(
                "درخواستی برای بازیابی رمز عبور حساب شما ثبت شده است. "
                "برای انتخاب رمز جدید روی دکمه‌ی زیر بزنید."
            ),
            cta_text="تغییر رمز عبور",
            cta_url=reset_link,
        ),
    )


def send_verification_email(to_email: str, verify_url: str) -> bool:
    return send_email(
        to_email=to_email,
        subject="تأیید ایمیل جارویس",
        html=_wrap_html(
            title_fa="تأیید ایمیل",
            body_fa=("به جارویس خوش آمدید! برای فعال‌سازی حساب خود، ایمیل‌تان را تأیید کنید."),
            cta_text="تأیید ایمیل",
            cta_url=verify_url,
        ),
    )


def get_frontend_url() -> str:
    return (os.getenv("FRONTEND_URL") or "http://localhost:5173").rstrip("/")


def build_password_reset_link(token: str) -> str:
    return f"{get_frontend_url()}/reset-password?token={token}"


def build_email_verification_link(token: str) -> str:
    return f"{get_frontend_url()}/verify-email?token={token}"
