"""
memory_updater.py
-----------------
بعد از هر مکالمه از GapGPT (OpenAI-compatible) می‌خواهد اطلاعات جدید را استخراج کند
و در memory_schema ادغام کند.
"""

import json
import re
from typing import Optional


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
- daily_state.current_tasks (لیست)
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
    یک GapGPT call سریع می‌زند و فیلدهای به‌روز شده را برمی‌گرداند.
    client باید openai.OpenAI با base_url گپ‌جی‌پی‌تی باشد.
    """
    prompt = MEMORY_UPDATE_PROMPT.format(
        current_memory=json.dumps(current_memory, ensure_ascii=False, indent=2),
        user_message=user_message,
        assistant_message=assistant_message[:600],
    )

    try:
        response = client.chat.completions.create(
            model="gpt-5.3-chat-latest",
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
