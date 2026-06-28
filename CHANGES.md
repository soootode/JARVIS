# خلاصه تغییرات

## فایل‌های تغییریافته فرانت‌اند

### ChatView.jsx ✅
- حذف dead-code (شرط `Message received` که به باگ قدیمی بک‌اند مربوط بود)
- استفاده از `Date.now()` برای id پیام‌ها به جای index (جلوگیری از key collision)
- `onKeyPress` → `onKeyDown` (onKeyPress deprecated است)
- دکمه ارسال وقتی input خالیه هم disabled می‌شه
- `whitespace-pre-wrap` به پیام‌ها اضافه شد (متن چندخطی درست نمایش داده می‌شه)

### DailyView.jsx ✅
- حذف `alert()` → کامپوننت `Toast` با انیمیشن (3 ثانیه auto-dismiss)
- دکمه ثبت فیدبک وقتی textarea خالیه هم disabled می‌شه

### WeeklyView.jsx ✅
- حذف `prompt()` → کامپوننت `CellEditor` با input inline
- موبایل‌فرندلی: کیبورد مجازی درست کار می‌کنه
- Enter برای ذخیره، Escape برای لغو
- کلیک روی سلول پر → ویرایش (نه پاک کردن)
- راست‌کلیک هنوز حذف می‌کنه

---

## فایل‌های جدید

### NotificationPoller.jsx ✅
کامپوننت polling که هر 30 ثانیه بک‌اند رو چک می‌کنه.
در App.jsx اضافه کن:
```jsx
import NotificationPoller from './components/NotificationPoller';

// داخل return:
<NotificationPoller />
```

### notification_endpoints_add_to_main.py
دو endpoint که باید به main.py اضافه بشن:
- `GET /api/notifications/pending` → نوتیف‌های pending رو برمی‌گردونه
- `POST /api/notifications/{id}/dismiss` → نوتیف رو mark-as-sent می‌کنه

---

## وضعیت نوتیفیکیشن

| لایه | وضعیت | توضیح |
|------|--------|-------|
| ذخیره reminder در DB | ✅ کار می‌کنه | از طریق `/api/reminders` |
| scheduler mark-as-sent | ✅ کار می‌کنه | هر 60 ثانیه |
| تحویل به فرانت‌اند | ❌ وجود نداشت | با polling حل شد |
| نمایش در UI | ❌ وجود نداشت | NotificationPoller.jsx اضافه شد |

Push notification واقعی (با Service Worker) نیاز به HTTPS دارد.
برای MVP لوکال polling کافیه.
