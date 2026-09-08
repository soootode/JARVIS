// src/pages/LandingPage.jsx
// هماهنگ‌شده دقیقاً با index (2).html — پس‌زمینه مشکی، فونت IBM Plex Sans
// Arabic، دکمه‌های خط‌کشی‌دستی، و ربات خطی بالای عنوان.
import { Link } from 'react-router-dom';
import SketchButton from '../components/ui/SketchButton';
import RobotAvatar from '../components/RobotAvatar';

const FONT_LINK_ID = 'jarvis-sketch-font';

const useSketchFont = () => {
  if (typeof document === 'undefined') return;
  if (document.getElementById(FONT_LINK_ID)) return;
  const link = document.createElement('link');
  link.id = FONT_LINK_ID;
  link.rel = 'stylesheet';
  link.href = 'https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&display=swap';
  document.head.appendChild(link);
};

const FEATURES = [
  { title: 'برنامه‌ریزی هوشمند', desc: 'یه هدف بهش بده، جارویس تبدیلش می‌کنه به یه برنامه روزانه و هفتگی قابل اجرا.' },
  { title: 'برنامه‌ای متناسب با واقعیت', desc: 'به‌جای برنامه‌ی آرمانی، بر اساس همون کاری که واقعاً انجام دادی برنامه‌ی بعدی رو می‌چینه.' },
  { title: 'همراهی در اجرا', desc: 'با یادآوری و پیگیری، کمکت می‌کنه برنامه فقط روی کاغذ نمونه.' },
  { title: 'یادگیری از تو', desc: 'هرچی بیشتر باهاش کار کنی، بهتر می‌شناستت و پیشنهادهاش شخصی‌تر می‌شه.' },
];

const LandingPage = () => {
  useSketchFont();

  return (
    <div
      className="min-h-screen bg-zinc-950 text-white"
      dir="rtl"
      style={{ fontFamily: "'IBM Plex Sans Arabic', sans-serif" }}
    >
      {/* NAV */}
      <nav className="max-w-4xl mx-auto flex items-center justify-between px-6 py-8">
        <span className="text-lg tracking-wide">جارویس</span>
        <div className="flex items-center gap-6">
          <Link to="/login" className="text-sm text-white/60 hover:text-white transition-colors">
            ورود
          </Link>
          <SketchButton to="/signup" variant="filled">ثبت‌نام</SketchButton>
        </div>
      </nav>

      {/* HERO */}
      <header className="max-w-4xl mx-auto px-6 pt-16 pb-20 text-center">
        <div className="mx-auto mb-8 flex justify-center">
          <RobotAvatar emotionalState="normal" size="large" />
        </div>
        <h1 className="text-4xl md:text-5xl font-light leading-tight mb-6">
          برنامه‌ت رو بساز، جارویس همراهته
        </h1>
        <p className="text-white/50 text-lg leading-relaxed max-w-md mx-auto mb-12">
          جارویس هدف و زمانت رو می‌گیره، برات برنامه می‌سازه و بر اساس چیزی که واقعاً انجام می‌دی، کمکت می‌کنه ادامه بدی.
        </p>
        <SketchButton to="/signup" variant="outline">شروع رایگان</SketchButton>
      </header>

      {/* FEATURES */}
      <section className="max-w-3xl mx-auto px-6 pb-24">
        <div className="grid md:grid-cols-2 gap-x-12 gap-y-10">
          {FEATURES.map((f) => (
            <div key={f.title} className="border-t border-zinc-800 pt-5">
              <h3 className="text-base font-medium mb-1.5">{f.title}</h3>
              <p className="text-sm text-white/45 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-2xl mx-auto px-6 pb-32 text-center">
        <p className="text-white/40 text-sm mb-6">مسیرت رو شروع کن.</p>
        <SketchButton to="/signup" variant="filled">شروع با جارویس</SketchButton>
      </section>

      <footer className="text-center text-xs text-white/25 pb-10">جارویس</footer>
    </div>
  );
};

export default LandingPage;
