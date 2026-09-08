# Jarvis-You — راهنمای اجرا

## بک‌اند
cd backend
python -m venv venv
venv\Scripts\activate      # ویندوز
pip install -r requirements.txt
# .env بساز (نمونه‌اش .env.example هست) و مقادیر زیر را پر کن:
#   - GOOGLE_API_KEY   → از https://aistudio.google.com/apikey
#   - JWT_SECRET_KEY   → با این بساز: python -c "import secrets; print(secrets.token_hex(32))"
#   - CRON_SECRET      → با این بساز: python -c "import secrets; print(secrets.token_urlsafe(32))"
uvicorn main:app --reload

## فرانت‌اند
cd frontend
npm install
# .env بساز (نمونه‌اش .env.example هست):
# VITE_API_BASE=http://localhost:8000
npm run dev

## دیپلوی

### بک‌اند: Vercel Serverless
- بک‌اند روی Vercel به‌عنوان Serverless Function دیپلوی می‌شه (`vercel.json` آماده‌ست).
- دیتابیس پروداکشن: **Supabase (PostgreSQL)** — از کانکشن‌استرینگ pooled (پورت 6543،
  درایور `postgresql+psycopg://`) استفاده کن تا Serverless connection limit سوپابیس رو
  خالی نکنی. جزئیات در `backend/.env.example`.
- یادآورها (Reminders) روی Vercel به‌جای APScheduler داخل‌پردازه، با یک
  **Vercel Cron Job** هر ۱۰ دقیقه به `GET /api/cron/check-reminders` می‌رسن
  (تعریف‌شده در `vercel.json`). این endpoint با هدر
  `Authorization: Bearer <CRON_SECRET>` محافظت می‌شه.
- روی Vercel، `VERCEL=1` به‌صورت خودکار توسط پلتفرم ست می‌شه و باعث می‌شه:
  - `database.py` از `NullPool` (بدون نگه‌داشتن کانکشن باز بین درخواست‌ها) استفاده کنه.
  - `main.py` استارت‌آپ اسکجولر داخل‌پردازه‌ای (APScheduler) رو skip کنه، چون توی
    Serverless بی‌فایده و پرهزینه‌ست.
- برای دیپلوی روی یک سرور سنتی/طولانی‌مدت (VM، Docker، bare uvicorn) به‌جای Vercel،
  همین کد بدون تغییر کار می‌کنه: `VERCEL` ست نمی‌شه، پس APScheduler و connection
  pooling معمولی (`pool_size`/`max_overflow`) به‌جای NullPool فعال می‌مونن.

### فرانت‌اند: Vercel
- فرانت‌اند: Vercel (vercel.json برای SPA routing آماده‌ست)
- بعد از دیپلوی فرانت‌اند، آدرسش رو به‌عنوان `FRONTEND_ORIGIN` توی env بک‌اند اضافه کن (برای CORS)
- بعد از دیپلوی بک‌اند، آدرسش رو به‌عنوان `VITE_API_BASE` توی env فرانت‌اند (روی Vercel) بذار

### AI Provider: Google Gemini
- سرویس LLM به **Google Gemini رسمی** متصل می‌شه، از طریق endpoint سازگار با OpenAI
  که گوگل ارائه می‌ده
  (`https://generativelanguage.googleapis.com/v1beta/openai/`). فقط یک
  `GOOGLE_API_KEY` لازمه — کد فراخوانی (`client.chat.completions.create(...)`)
  در `main.py`، `memory_updater.py` و `scheduler_service.py` بدون تفییر می‌مونه.
