// src/components/ui/SketchPanel.jsx
// جایگزین کارت‌های سفید rounded-2xl shadow-lg قبلی — یه باکس با خط نازک،
// پس‌زمینه شفاف (روی مشکی)، بدون سایه.
const SketchPanel = ({ children, className = '' }) => (
  <div className={`border border-zinc-800 rounded-lg p-5 ${className}`}>
    {children}
  </div>
);

export default SketchPanel;
