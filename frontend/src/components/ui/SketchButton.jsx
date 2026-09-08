// src/components/ui/SketchButton.jsx
// دکمه‌ی مشترک با استایل خط‌کشی‌دستی — استفاده در همه‌ی صفحات (لندینگ، اپ اصلی).
// variant="filled" => پرشده با سفید، متن مشکی. variant="outline" (پیش‌فرض) => فقط خط، متن سفید.
import { Link } from 'react-router-dom';

const SketchButton = ({
  children,
  to,
  href,
  variant = 'outline',
  type = 'button',
  onClick,
  disabled = false,
  small = false,
  className = '',
}) => {
  const isFilled = variant === 'filled';
  const base = `relative inline-flex items-center justify-center ${small ? 'px-5 py-2 text-xs' : 'px-8 py-3 text-sm'} group disabled:opacity-40 disabled:cursor-not-allowed ${className}`;
  const content = (
    <>
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none"
        viewBox="0 0 200 56"
        preserveAspectRatio="none"
        style={{ overflow: 'visible' }}
      >
        <path
          d="M 4 6 C 40 3, 120 8, 196 5 C 199 20, 197 38, 197 50 C 150 53, 60 51, 3 52 C 1 38, 3 18, 4 6 Z"
          fill={isFilled ? '#ffffff' : 'none'}
          stroke="#ffffff"
          strokeWidth="1.4"
          className={disabled ? '' : 'transition-all duration-200 group-hover:stroke-[1.8]'}
        />
      </svg>
      <span className={`relative z-10 tracking-wide ${isFilled ? 'text-black font-medium' : 'text-white'}`}>
        {children}
      </span>
    </>
  );

  if (to) {
    return (
      <Link to={to} className={base}>
        {content}
      </Link>
    );
  }
  if (href) {
    return (
      <a href={href} className={base}>
        {content}
      </a>
    );
  }
  return (
    <button type={type} onClick={onClick} disabled={disabled} className={base}>
      {content}
    </button>
  );
};

export default SketchButton;
