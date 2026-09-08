"""
memory_updater.py
-----------------
<<<<<<< HEAD
بعد از هر مکالمه از Google Gemini (از طریق endpoint سازگار با OpenAI) می‌خواهد
اطلاعات جدید را استخراج کند و در memory_schema ادقام کند.
"""

import json
import os
import re
from typing import Optional

# هماهنگ با MODEL توی main.py — یه‌جا از env خونده می‌شه، نه هاردکد جدا جدا.
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.6-flash")

=======
بعد از هر مکالمه از GapGPT (OpenAI-compatible) می‌خواهد اطلاعات جدید را استخراج کند
و در memory_schema ادغام کند.
"""

import json
import re
from typing import Optional

>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9

MEMORY_UPDATE_PROMPT = """
تو یک سیستم استخراج اطلاعات هستی.
وظیفه‌ات این است که از یک مکالمه کوتاه، اطلاعات قابل ذخیره درباره کاربر را پیدا کنی
و فقط آن‌ها را به فرمت JSON برگردانی.

حافظه فعلی کاربر:
{current_memory}

مکالمه اخیر:
کاربر: {user_message}
دستیار: {assistant_message}

وظیفه:
فقط اطلاعات جدید یا تغییریافته را استخراج کن.
فقط از این کلیدها استفاده کن:
- daily_state.mood
- daily_state.energy
- daily_state.stress_level
<<<<<<< HEAD
=======
- daily_state.current_tasks (لیست)
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
- daily_state.blockers (لیست)
- psychology.stress_triggers (لیست - فقط موارد جدید)
- psychology.motivators (لیست - فقط موارد جدید)
- behavioral_memory.habits_positive (لیست)
- behavioral_memory.habits_negative (لیست)
- events.wins (لیست)
- events.setbacks (لیست)
- task_history.completed_tasks (لیست)

قوانین:
1. اگر هیچ اطلاعات جدیدی نیست، فقط بنویس: null
2. فقط JSON خالص بده، بدون توضیح یا markdown
3. فقط اطلاعات صریح و واضح را ذخیره کن

نمونه خروجی:
{{"daily_state": {{"mood": "خسته", "stress_level": "بالا"}}, "events": {{"wins": ["ریاضی گسسته تمام شد"]}}}}

خروجی (فقط JSON یا null):
"""


def extract_memory_updates(
    client,
    user_message: str,
    assistant_message: str,
    current_memory: dict,
) -> Optional[dict]:
    """
<<<<<<< HEAD
    یک درخواست سریع به مدل (Google Gemini) می‌زند و فیلدهای به‌روز شده را برمی‌گرداند.
    client باید openai.OpenAI با base_url مربوط به Gemini باشد
    (https://generativelanguage.googleapis.com/v1beta/openai/).
=======
    یک GapGPT call سریع می‌زند و فیلدهای به‌روز شده را برمی‌گرداند.
    client باید openai.OpenAI با base_url گپ‌جی‌پی‌تی باشد.
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
    """
    prompt = MEMORY_UPDATE_PROMPT.format(
        current_memory=json.dumps(current_memory, ensure_ascii=False, indent=2),
        user_message=user_message,
        assistant_message=assistant_message[:600],
    )

    try:
        response = client.chat.completions.create(
<<<<<<< HEAD
            model=LLM_MODEL,
=======
            model="gpt-5.3-chat-latest",
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
            messages=[
                {
                    "role": "system",
                    "content": "تو یک سیستم استخراج اطلاعات هستی. فقط JSON خالص یا null برمی‌گردانی.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=512,
        )
        raw = response.choices[0].message.content.strip()

        if raw.lower() in ("null", "none", ""):
            return None

        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        updates = json.loads(raw)
        return updates if isinstance(updates, dict) else None

    except Exception as e:
        print(f"⚠️ memory update skipped: {e}")
        return None


<<<<<<< HEAD
REFLECTION_DETECTION_PROMPT = """
تو یک روان‌شناس تحلیل‌گر دقیق و محتاط هستی، نه یک قضاوت‌گر.

پروفایل روان‌شناختی self-reported کاربر (چیزی که خودش درباره‌ی خودش گفته):
{psychology_profile}

آمار رفتاری عینی اخیرش (از داده‌ی واقعی سیستم، نه خوداظهاری):
{behavior_snapshot}

وظیفه:
بررسی کن آیا بین رفتار عینی و پروفایل self-reported یک تناقض *معنادار و قابل‌اتکا*
وجود داره یا نه. مثال‌های تناقض معنادار:
- کاربر می‌گه "سبک کاریم پروژه‌محوره" ولی نرخ رهاکردن پروژه بالاست
- کاربر هیچ اشاره‌ای به تعلل نکرده ولی نرخ تکمیل تسک خیلی پایینه
- الگویی که آمار نشون می‌ده ولی توی self-report اصلاً ثبت نشده

قوانین سخت‌گیرانه:
1. فقط وقتی سیگنال قوی، مکرر، و بدون توضیح واضح دیگه‌ای (مثل تعطیلات، بیماری) باشه، تناقض اعلام کن.
2. نوسان‌های کوچیک یا داده‌ی ناکافی رو نادیده بگیر — این باید محافظه‌کارانه باشه.
3. اگه تناقض واقعی پیدا کردی، یک سوال بازتابی کوتاه (۲-۳ جمله)، محترمانه، بدون قضاوت،
   و به زبان فارسی محاوره‌ای بنویس که جارویس بتونه طبیعی توی چت مطرح کنه.
4. هیچوقت تشخیص بالینی یا برچسب روان‌شناختی («تو افسردگی داری») نده — فقط الگوی رفتاری رو منعکس کن.
5. اگه هیچ تناقض قابل‌اتکایی نیست، دقیقاً بنویس: null

خروجی (فقط متن سوال فارسی، یا کلمه‌ی null — بدون توضیح یا markdown):
"""


def detect_behavioral_reflection(
    client,
    psychology_profile: dict,
    behavior_snapshot: dict,
) -> Optional[str]:
    """
    برخلاف extract_memory_updates (که فقط append می‌کنه)، این تابع صراحتاً
    رفتار عینی رو در برابر خوداظهاری می‌سنجه و اگه LLM تناقض معناداری
    تشخیص بده، متن سوال بازتابی رو برمی‌گردونه.

    این جایگزین قوانین دستی نیست — مکملشه: caller (memory_manager) باید
    اگه این تابع None برگردوند یا exception داد، fallback کنه به همون
    قوانین آماری ساده (که رایگان و همیشه در دسترسه).
    """
    prompt = REFLECTION_DETECTION_PROMPT.format(
        psychology_profile=json.dumps(psychology_profile, ensure_ascii=False, indent=2),
        behavior_snapshot=json.dumps(behavior_snapshot, ensure_ascii=False, indent=2, default=str),
    )

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "تو یک روان‌شناس تحلیل‌گر محتاط هستی. فقط متن سوال یا کلمه‌ی null برمی‌گردانی.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=300,
        )
        raw = response.choices[0].message.content.strip()

        if raw.lower().strip(".، ") in ("null", "none", ""):
            return None

        raw = re.sub(r"^```(?:text)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        raw = raw.strip("\"' \n")

        return raw or None

    except Exception as e:
        print(f"⚠️ reflection detection skipped (fallback to rule-based): {e}")
        return None


BELIEF_REVISION_PROMPT = """
تو یک تحلیل‌گر دقیق هستی که تشخیص می‌دی آیا جواب یک کاربر به یک سوال بازتابی،
واقعاً باور قبلیش رو تغییر داده یا نه.

سوالی که به کاربر مطرح شد:
{reflection_question}

جواب کاربر:
{user_reply}

پروفایل روان‌شناختی فعلی کاربر (برای زمینه):
{current_psychology}

وظیفه:
مشخص کن آیا این جواب یک تغییر واقعی و صریح در باور کاربر نشون می‌ده یا نه.
مثال‌هایی که تغییر واقعی حساب می‌شن:
- "آره حق داری، فکر نمی‌کنم دیگه پروژه‌محور باشم" (تایید صریح تغییر)
- "راستش نه، فکر می‌کنم مشکل از جای دیگه‌ست، شاید ابهام تسک‌هاست" (اصلاح با توضیح جدید)

مثال‌هایی که تغییر واقعی *نیستن* (باید null برگردونی):
- جواب کوتاه بی‌ربط یا فرار از سوال ("بعداً بهش فکر می‌کنم")
- کاربر فقط سوال رو تایید کرد بدون هیچ توضیح جدیدی درباره‌ی خودش
- کاربر موضوع رو عوض کرد

اگه تغییر واقعی تشخیص دادی، دقیقاً این ساختار JSON رو برگردون:
{{"field_name": "...", "old_value_summary": "...", "new_value": "...", "confidence": "high|medium|low"}}

field_name باید یکی از این‌ها باشه: stress_triggers, motivators, fear_patterns,
procrastination_patterns, communication_style, decision_making_style

اگه تغییر واقعی نیست، فقط بنویس: null

خروجی (فقط JSON یا null، بدون توضیح یا markdown):
"""


def extract_belief_revision(
    client,
    reflection_question: str,
    user_reply: str,
    current_psychology: dict,
) -> Optional[dict]:
    """
    لایه‌ی ۵ داربست شناختی (حلقه‌ی بسته): وقتی کاربر به یک سوال بازتابی
    جواب می‌ده، این تابع تشخیص می‌ده آیا این جواب واقعاً یه باور
    self-reported رو اصلاح می‌کنه یا نه. برخلاف extract_memory_updates
    (که چیز جدید append می‌کنه)، این صراحتاً دنبال *تغییر* یه باور موجوده.

    محافظه‌کارانه طراحی شده: در صورت شک، None برمی‌گردونه — چون یه
    بازنویسی نادرست باور بدتر از یه بازنویسی ازدست‌رفته‌ست.
    """
    prompt = BELIEF_REVISION_PROMPT.format(
        reflection_question=reflection_question,
        user_reply=user_reply[:600],
        current_psychology=json.dumps(current_psychology, ensure_ascii=False, indent=2),
    )

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "تو فقط JSON خالص یا null برمی‌گردونی. هیچ توضیح اضافه نده.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=300,
        )
        raw = response.choices[0].message.content.strip()

        if raw.lower().strip(".، ") in ("null", "none", ""):
            return None

        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        result = json.loads(raw)
        if not isinstance(result, dict) or "field_name" not in result:
            return None
        return result

    except Exception as e:
        print(f"⚠️ belief revision extraction skipped: {e}")
        return None


=======
>>>>>>> 9ff17d3b7c338f01fb187fca8733efaa93c538b9
def apply_updates(memory: dict, updates: dict) -> dict:
    """
    فیلدهای جدید را روی memory اعمال می‌کند.
    لیست‌ها: append (بدون تکرار)
    رشته‌ها: replace
    """
    for section_key, section_val in updates.items():
        if not isinstance(section_val, dict):
            continue
        if section_key not in memory:
            memory[section_key] = {}
        for field_key, field_val in section_val.items():
            existing = memory[section_key].get(field_key)
            if isinstance(field_val, list):
                if not isinstance(existing, list):
                    memory[section_key][field_key] = []
                for item in field_val:
                    if item not in memory[section_key][field_key]:
                        memory[section_key][field_key].append(item)
            else:
                memory[section_key][field_key] = field_val
    return memory
