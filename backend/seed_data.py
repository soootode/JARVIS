"""
seed_data.py - Jarvis-You
تزریق داده‌های اولیه از persona.json به دیتابیس
ایمن در برابر اجرای چندباره (Upsert منطق)
"""

import json
from datetime import datetime, timedelta
from database import init_db, get_session, Persona, Psychology, Goal, Habit

# ── رنگ‌بندی ترمینال ──────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def log_section(title: str):
    print(f"\n{BOLD}{CYAN}{'─'*50}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─'*50}{RESET}")

def log_ok(msg: str):
    print(f"  {GREEN}✓{RESET} {msg}")

def log_skip(msg: str):
    print(f"  {YELLOW}↷{RESET} {msg} (از قبل موجود، آپدیت شد)")


# ══════════════════════════════════════════════════════════════════════════════
# ۱. Persona
# ══════════════════════════════════════════════════════════════════════════════

def seed_persona(db) -> None:
    log_section("لایه ۱ · Persona (هویت)")

    identity = DATA["identity"]
    background = identity.get("background", {})

    existing = db.get(Persona, 1)
    is_new = existing is None

    p = existing or Persona(id=1)
    p.preferred_name   = identity.get("preferred_name", "ستوده")
    p.age              = identity.get("age", 24)
    p.gender           = "زن"
    p.location         = "تهران، ایران"
    p.occupation       = background.get("education", "")
    p.education_level  = background.get("education", "")
    p.languages        = json.dumps(["fa", "en"], ensure_ascii=False)
    p.core_values      = json.dumps(
        DATA.get("core_personality", {}).get("values", []),
        ensure_ascii=False,
    )
    p.life_philosophy  = background.get("long_term_vision", "")
    p.mbti             = "INTJ"   # از شخصیت‌نامه استنتاج‌شده
    p.enneagram        = "5w4"    # از شخصیت‌نامه استنتاج‌شده
    p.updated_at       = datetime.utcnow()

    if is_new:
        db.add(p)
        log_ok(f"Persona ساخته شد → {p.preferred_name}، {p.age} ساله")
    else:
        log_skip(f"Persona → {p.preferred_name}")


# ══════════════════════════════════════════════════════════════════════════════
# ۲. Psychology
# ══════════════════════════════════════════════════════════════════════════════

def seed_psychology(db) -> None:
    log_section("لایه ۱ · Psychology (پروفایل روان‌شناختی)")

    psych_data   = DATA.get("psychological_profile", {})
    cognitive    = DATA.get("cognitive_profile", {})
    core         = DATA.get("core_personality", {})
    motivational = DATA.get("motivational_system", {})

    existing = db.get(Psychology, 1)
    is_new   = existing is None
    ps       = existing or Psychology(id=1)

    ps.stress_triggers = json.dumps(
        psych_data.get("emotional_triggers", []), ensure_ascii=False
    )
    ps.motivators = json.dumps(
        motivational.get("drivers", []), ensure_ascii=False
    )
    ps.fear_patterns = json.dumps(
        [
            "ترس از کم‌هوشی و نابسندگی",
            "ترس از شکست علمی",
            "ترس از جایگزین شدن و ترک شدن",
            "ترس از پایان دادن کارها به خاطر ابهام",
        ],
        ensure_ascii=False,
    )
    ps.cognitive_biases = json.dumps(
        cognitive.get("execution_challenges", []), ensure_ascii=False
    )
    ps.coping_strategies = json.dumps(
        psych_data.get("regulation_needs", []), ensure_ascii=False
    )
    ps.attachment_style       = psych_data.get("attachment_style", "")
    ps.communication_style    = "تحلیلی، درونی‌گرا، نیاز به شفافیت و صراحت"
    ps.decision_making_style  = "اطلاعات‌محور – در شرایط ابهام دچار freeze می‌شود"
    ps.procrastination_patterns = json.dumps(
        [
            "انرژی اولیه زیاد → فرسودگی سریع → رها کردن",
            "ابهام → توقف کامل",
            "اضطراب → overthinking → freeze",
            "باور ناخودآگاه که آرامش = نتیجه بد",
        ],
        ensure_ascii=False,
    )
    ps.updated_at = datetime.utcnow()

    if is_new:
        db.add(ps)
        log_ok("Psychology ساخته شد")
        log_ok(f"  stress_triggers   : {len(psych_data.get('emotional_triggers', []))} مورد")
        log_ok(f"  motivators        : {len(motivational.get('drivers', []))} مورد")
        log_ok(f"  procrastination   : 4 الگوی اجرایی")
    else:
        log_skip("Psychology")


# ══════════════════════════════════════════════════════════════════════════════
# ۳. Goals
# ══════════════════════════════════════════════════════════════════════════════

GOAL_SPECS = [
    # (title, category, priority, timeframe, target_date_offset_days, milestones)
    # ── ۶ ماهه ──
    (
        "قبولی ارشد مهندسی کامپیوتر – دانشگاه شریف",
        "education", 1, "short", 180,
        [
            {"title": "اتمام ریاضی گسسته", "done": False},
            {"title": "اتمام ساختمان داده", "done": False},
            {"title": "اتمام الگوریتم", "done": False},
            {"title": "شرکت در آزمون کنکور ارشد", "done": False},
        ],
    ),
    (
        "بهبود ثبات عملکرد روزانه",
        "health", 2, "short", 180,
        [
            {"title": "ایجاد روتین صبحگاهی ثابت", "done": False},
            {"title": "ثبت وضعیت روزانه به‌صورت منظم", "done": False},
            {"title": "حفظ streak 30 روزه", "done": False},
        ],
    ),
    (
        "مدیریت اضطراب عملکرد",
        "health", 3, "short", 180,
        [
            {"title": "شناسایی trigger های اضطراب", "done": False},
            {"title": "یادگیری تکنیک‌های grounding", "done": False},
        ],
    ),
    (
        "تقویت مهارت‌های بنیادی CS (DS، الگوریتم، ریاضی گسسته)",
        "education", 4, "short", 180,
        [
            {"title": "ریاضی گسسته – کتاب رایزن و آزبورن", "done": False},
            {"title": "ساختمان داده – پیاده‌سازی عملی در پایتون", "done": False},
            {"title": "الگوریتم – حل 100 مسئله LeetCode", "done": False},
        ],
    ),
    # ── ۱ ساله ──
    (
        "شروع مسیر بیوانفورماتیک",
        "career", 5, "mid", 365,
        [
            {"title": "پذیرش در ارشد کامپیوتر/بیوانفورماتیک", "done": False},
            {"title": "مطالعه زیست‌شناسی مولکولی پایه", "done": False},
            {"title": "یادگیری Biopython", "done": False},
        ],
    ),
    (
        "ساخت Jarvis-You – دستیار هوشمند شخصی",
        "career", 6, "mid", 365,
        [
            {"title": "Milestone 1: FastAPI + Gemini + Memory", "done": True},
            {"title": "Milestone 2: SQLAlchemy + سه‌لایه حافظه", "done": False},
            {"title": "Milestone 3: فرانت‌اند React", "done": False},
            {"title": "Milestone 4: دیپلوی روی لیارا", "done": False},
        ],
    ),
    (
        "بازسازی نظم شخصی و تحصیلی",
        "health", 7, "mid", 365,
        [
            {"title": "ایجاد سیستم مدیریت زمان پایدار", "done": False},
            {"title": "ترمیم عزت نفس علمی", "done": False},
        ],
    ),
    # ── بلندمدت ──
    (
        "ورود به حوزه درمان‌های شخصی‌سازی‌شده و Drug Discovery",
        "career", 8, "long", 365 * 5,
        [
            {"title": "فارغ‌التحصیلی ارشد بیوانفورماتیک", "done": False},
            {"title": "انتشار اولین paper پژوهشی", "done": False},
            {"title": "کار روی مدل‌های ML برای دراگ‌دیسکاوری", "done": False},
        ],
    ),
    (
        "اثرگذاری بلندمدت علمی در علم و تکنولوژی زیستی",
        "career", 9, "long", 365 * 7,
        [
            {"title": "تأسیس یا عضویت در یک تیم پژوهشی مستقل", "done": False},
            {"title": "پروژه‌های واقعی در سطح بین‌المللی", "done": False},
        ],
    ),
]


def seed_goals(db) -> None:
    log_section("لایه ۱ · Goals (اهداف)")

    now = datetime.utcnow()
    created = updated = 0

    for title, category, priority, timeframe, offset_days, milestones in GOAL_SPECS:
        existing = db.query(Goal).filter_by(title=title).first()

        if existing:
            existing.category         = category
            existing.priority         = priority
            existing.timeframe        = timeframe
            existing.target_date      = now + timedelta(days=offset_days)
            existing.milestones       = json.dumps(milestones, ensure_ascii=False)
            existing.status           = "active"
            existing.updated_at       = now
            log_skip(f"Goal → {title[:55]}")
            updated += 1
        else:
            g = Goal(
                title=title,
                category=category,
                priority=priority,
                timeframe=timeframe,
                target_date=now + timedelta(days=offset_days),
                milestones=json.dumps(milestones, ensure_ascii=False),
                status="active",
                progress_percent=0.0,
            )
            db.add(g)
            log_ok(f"Goal → {title[:55]}")
            created += 1

    print(f"\n  {GREEN}→ جمع: {created} ساخته شد، {updated} آپدیت شد{RESET}")


# ══════════════════════════════════════════════════════════════════════════════
# ۴. Habits
# ══════════════════════════════════════════════════════════════════════════════

HABIT_SPECS = [
    # (name, habit_type, frequency, target_count, category, description)
    (
        "مطالعه پالس متمرکز – آمادگی ارشد کامپیوتر",
        "positive", "daily", 2, "study",
        "حداقل ۲ پالس ۴۵ دقیقه‌ای مطالعه متمرکز روی دروس کنکور ارشد "
        "(ریاضی گسسته / ساختمان داده / الگوریتم). "
        "بدون گوشی، بدون تب‌های اضافه.",
    ),
    (
        "ثبت وضعیت روزانه در Jarvis",
        "positive", "daily", 1, "self_awareness",
        "هر روز صبح یا شب، خلق، انرژی، استرس و تسک‌های امروز را در دستیار ثبت کن. "
        "این داده‌ها به Jarvis کمک می‌کند الگوهای تو را بشناسد.",
    ),
    (
        "ورزش / حرکت بدنی",
        "positive", "daily", 1, "health",
        "حداقل ۲۰ دقیقه حرکت بدنی: پیاده‌روی، کشش، یوگا یا هر چیزی که بدن را فعال کند. "
        "هدف: کاهش تنش شناختی انباشته.",
    ),
    (
        "مرور شبانه – چه کردم؟",
        "positive", "daily", 1, "self_awareness",
        "قبل از خواب، ۵ دقیقه: ۱ چیزی که تمام کردم، ۱ چیزی که گیر کردم، فردا چه می‌کنم. "
        "هدف: ایجاد هویت finisher و کاهش اضطراب شبانه.",
    ),
    (
        "دوم‌زدن به شبکه‌های اجتماعی در ساعت مطالعه",
        "negative", "daily", 0, "focus",
        "باز کردن اینستاگرام، توییتر یا تلگرام غیرضروری در بلوک‌های مطالعه. "
        "اگر این عادت رخ داد، ثبت کن تا الگو شناخته شود.",
    ),
    (
        "شروع و رها کردن تسک بدون اتمام",
        "negative", "daily", 0, "execution",
        "شروع کردن یک کار جدید قبل از اتمام کار قبلی. "
        "ثبت این رفتار به Jarvis کمک می‌کند الگوی پرش تسک را رصد کند.",
    ),
]


def seed_habits(db) -> None:
    log_section("لایه ۲ · Habits (عادت‌ها)")

    created = updated = 0

    for name, habit_type, frequency, target_count, category, description in HABIT_SPECS:
        existing = db.query(Habit).filter_by(name=name).first()

        if existing:
            existing.habit_type   = habit_type
            existing.frequency    = frequency
            existing.target_count = target_count
            existing.category     = category
            existing.description  = description
            existing.is_active    = True
            existing.updated_at   = datetime.utcnow()
            log_skip(f"Habit → {name[:55]}")
            updated += 1
        else:
            h = Habit(
                name=name,
                description=description,
                habit_type=habit_type,
                frequency=frequency,
                target_count=target_count,
                category=category,
                is_active=True,
                streak_current=0,
                streak_best=0,
            )
            db.add(h)
            log_ok(f"Habit [{habit_type:8s}] → {name[:50]}")
            created += 1

    print(f"\n  {GREEN}→ جمع: {created} ساخته شد، {updated} آپدیت شد{RESET}")


# ══════════════════════════════════════════════════════════════════════════════
# Main Runner
# ══════════════════════════════════════════════════════════════════════════════

def run_seed() -> None:
    print(f"\n{BOLD}{'═'*52}")
    print("  Jarvis-You · Seed Data")
    print(f"{'═'*52}{RESET}")
    print(f"  زمان اجرا : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ── بارگذاری persona.json ──────────────────────────────────────────────
    import os
    persona_path = os.path.join(os.path.dirname(__file__), "persona.json")
    if not os.path.exists(persona_path):
        print(f"\n  ❌ فایل persona.json پیدا نشد در: {persona_path}")
        return

    global DATA
    with open(persona_path, "r", encoding="utf-8") as f:
        DATA = json.load(f)
    print(f"  persona.json  : بارگذاری شد ✓")

    # ── ساخت جداول (ایمن در برابر تکرار) ─────────────────────────────────
    init_db()
    print(f"  جداول دیتابیس: آماده ✓")

    # ── Seed با تراکنش ─────────────────────────────────────────────────────
    db = get_session()
    try:
        seed_persona(db)
        seed_psychology(db)
        seed_goals(db)
        seed_habits(db)

        db.commit()
        print(f"\n{BOLD}{GREEN}{'═'*52}")
        print("  ✅ Seed کامل شد — دیتابیس آماده است")
        print(f"{'═'*52}{RESET}\n")

    except Exception as e:
        db.rollback()
        print(f"\n{BOLD}\033[91m{'═'*52}")
        print(f"  ❌ خطا در Seed: {e}")
        print(f"{'═'*52}{RESET}\n")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
