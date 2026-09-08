// src/pages/OnboardingWizard.jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiJson } from '../lib/apiClient';
import { useAuth } from '../context/AuthContext';
import SketchButton from '../components/ui/SketchButton';
import { SketchInput, SketchTextarea } from '../components/ui/SketchInput';

const STEPS = ['identity', 'values', 'style', 'challenges', 'motivators'];

const emptyForm = {
  preferred_name: '',
  age: '',
  occupation: '',
  education_level: '',
  life_philosophy: '',
  core_values: '',
  learning_style: '',
  main_challenges: '',
  motivators: '',
};

const toList = (s) => s.split(',').map((x) => x.trim()).filter(Boolean);

const OnboardingWizard = () => {
  const navigate = useNavigate();
  const { markOnboardingComplete } = useAuth();
  const [stepIdx, setStepIdx] = useState(0);
  const [form, setForm] = useState(emptyForm);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const step = STEPS[stepIdx];
  const isLast = stepIdx === STEPS.length - 1;

  const update = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const canProceed = () => {
    if (step === 'identity') return form.preferred_name.trim().length > 0;
    return true;
  };

  const next = () => setStepIdx((i) => Math.min(i + 1, STEPS.length - 1));
  const prev = () => setStepIdx((i) => Math.max(i - 1, 0));

  const handleSubmit = async () => {
    setSubmitting(true);
    setError('');
    try {
      await apiJson('/api/onboarding', {
        method: 'POST',
        body: JSON.stringify({
          preferred_name: form.preferred_name.trim(),
          age: form.age ? Number(form.age) : null,
          occupation: form.occupation.trim() || null,
          education_level: form.education_level.trim() || null,
          life_philosophy: form.life_philosophy.trim() || null,
          core_values: toList(form.core_values),
          learning_style: form.learning_style.trim() || null,
          main_challenges: toList(form.main_challenges),
          motivators: toList(form.motivators),
        }),
      });
      markOnboardingComplete();
      navigate('/app', { replace: true });
    } catch (err) {
      setError(err.message || 'مشکلی پیش اومد. دوباره امتحان کن.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center bg-zinc-950 text-white px-4"
      dir="rtl"
      style={{ fontFamily: "'IBM Plex Sans Arabic', sans-serif" }}
    >
      <div className="w-full max-w-lg">
        {/* Progress dots */}
        <div className="flex items-center justify-center gap-2 mb-10">
          {STEPS.map((s, i) => (
            <div
              key={s}
              className={`h-1.5 rounded-full transition-all ${
                i === stepIdx ? 'w-8 bg-white' : 'w-1.5 bg-white/20'
              }`}
            />
          ))}
        </div>

        <div>
          {step === 'identity' && (
            <div className="space-y-6">
              <h2 className="text-lg font-medium">بذار بشناسیمت</h2>
              <div>
                <label className="block text-xs text-white/60 font-medium mb-1.5">اسمت چیه؟</label>
                <SketchInput autoFocus value={form.preferred_name} onChange={update('preferred_name')} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-white/60 font-medium mb-1.5">سن (اختیاری)</label>
                  <SketchInput type="number" value={form.age} onChange={update('age')} />
                </div>
                <div>
                  <label className="block text-xs text-white/60 font-medium mb-1.5">شغل / حوزه</label>
                  <SketchInput value={form.occupation} onChange={update('occupation')} />
                </div>
              </div>
              <div>
                <label className="block text-xs text-white/60 font-medium mb-1.5">تحصیلات</label>
                <SketchInput value={form.education_level} onChange={update('education_level')} />
              </div>
            </div>
          )}

          {step === 'values' && (
            <div className="space-y-6">
              <h2 className="text-lg font-medium">اهداف و ارزش‌ها</h2>
              <div>
                <label className="block text-xs text-white/60 font-medium mb-1.5">
                  فلسفه زندگی / چشم‌انداز بلندمدتت چیه؟
                </label>
                <SketchTextarea
                  rows={3}
                  value={form.life_philosophy}
                  onChange={update('life_philosophy')}
                />
              </div>
              <div>
                <label className="block text-xs text-white/60 font-medium mb-1.5">
                  ارزش‌های اصلیت چیه؟ (با ویرگول جدا کن)
                </label>
                <SketchInput
                  value={form.core_values}
                  onChange={update('core_values')}
                  placeholder="استقلال، پیشرفت علمی، اصالت"
                />
              </div>
            </div>
          )}

          {step === 'style' && (
            <div className="space-y-6">
              <h2 className="text-lg font-medium">سبک یادگیری‌ات چطوره؟</h2>
              <div>
                <label className="block text-xs text-white/60 font-medium mb-1.5">
                  چطور بهتر یاد می‌گیری / کار می‌کنی؟
                </label>
                <SketchTextarea
                  rows={3}
                  value={form.learning_style}
                  onChange={update('learning_style')}
                  placeholder="مثلاً: پروژه‌محور، نیاز به ساختار قدم‌به‌قدم"
                />
              </div>
            </div>
          )}

          {step === 'challenges' && (
            <div className="space-y-6">
              <h2 className="text-lg font-medium">چالش‌های اصلیت</h2>
              <div>
                <label className="block text-xs text-white/60 font-medium mb-1.5">
                  چی معمولاً باعث استرس یا گیر کردنت می‌شه؟ (با ویرگول جدا کن)
                </label>
                <SketchInput
                  value={form.main_challenges}
                  onChange={update('main_challenges')}
                  placeholder="ابهام در تسک‌ها، مهلت‌های فوری"
                />
              </div>
            </div>
          )}

          {step === 'motivators' && (
            <div className="space-y-6">
              <h2 className="text-lg font-medium">چی بهت انگیزه می‌ده؟</h2>
              <div>
                <label className="block text-xs text-white/60 font-medium mb-1.5">(با ویرگول جدا کن)</label>
                <SketchInput
                  value={form.motivators}
                  onChange={update('motivators')}
                  placeholder="پیشرفت روزانه، دیده شدن"
                />
              </div>
              <p className="text-xs text-white/45">
                همینه! جارویس از الان با این پروفایل شروع می‌کنه و هرچی بیشتر باهاش حرف بزنی، بیشتر می‌شناستت.
              </p>
            </div>
          )}
        </div>

        {error && <p className="text-sm text-red-400 mt-6">{error}</p>}

        <div className="flex items-center justify-between mt-12">
          <button
            onClick={prev}
            disabled={stepIdx === 0}
            className="text-sm text-white/55 hover:text-white disabled:opacity-20 transition-colors"
          >
            ← قبلی
          </button>

          {isLast ? (
            <SketchButton onClick={handleSubmit} variant="filled" disabled={submitting || !canProceed()}>
              {submitting ? 'در حال ذخیره...' : 'شروع کن'}
            </SketchButton>
          ) : (
            <SketchButton onClick={next} variant="outline" disabled={!canProceed()}>
              بعدی →
            </SketchButton>
          )}
        </div>
      </div>
    </div>
  );
};

export default OnboardingWizard;
