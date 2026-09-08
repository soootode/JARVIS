// src/components/ui/SketchInput.jsx
// جایگزین input های سفید rounded-xl قبلی — فقط یه خط زیرش، پس‌زمینه شفاف.
const baseClass =
  'w-full bg-transparent border-0 border-b border-white/25 focus:border-white/70 outline-none text-white placeholder-white/30 py-2 px-1 transition-colors';

export const SketchInput = (props) => <input {...props} className={`${baseClass} ${props.className || ''}`} />;

export const SketchTextarea = (props) => (
  <textarea {...props} className={`${baseClass} resize-none ${props.className || ''}`} />
);

export default SketchInput;
