// src/components/RobotAvatar.jsx
import { motion } from 'framer-motion';

const RobotAvatar = ({ emotionalState = 'normal', size = 'normal' }) => {
  const sizeMap = {
    small: { width: 60, height: 60 },
    normal: { width: 80, height: 80 },
    large: { width: 120, height: 120 }
  };

  const dimensions = sizeMap[size] || sizeMap.normal;

  const emotionConfig = {
    normal: { eyeScale: 1, bodyRotate: 0, eyeY: 0, smilePath: 'M 35 55 Q 50 60 65 55' },
    listening: { eyeScale: 0.8, bodyRotate: 5, eyeY: -2, smilePath: 'M 35 55 Q 50 58 65 55' },
    thinking: { eyeScale: 0.6, bodyRotate: -3, eyeY: 3, smilePath: 'M 35 57 Q 50 55 65 57' },
    happy: { eyeScale: 1.2, bodyRotate: 0, eyeY: -3, smilePath: 'M 35 52 Q 50 62 65 52' }
  };

  const config = emotionConfig[emotionalState] || emotionConfig.normal;

  return (
    <motion.div
      animate={{ y: [0, -8, 0] }}
      transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
      style={{ width: dimensions.width, height: dimensions.height }}
    >
      <motion.svg
        viewBox="0 0 100 100"
        animate={{ rotate: config.bodyRotate }}
        transition={{ duration: 0.5 }}
      >
        <defs>
          <linearGradient id="bodyGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="100%" stopColor="#e8e8e8" />
          </linearGradient>
          <filter id="shadow">
            <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.2"/>
          </filter>
        </defs>

        <motion.ellipse
          cx="50" cy="55" rx="28" ry="35"
          fill="url(#bodyGradient)"
          filter="url(#shadow)"
        />

        <motion.rect
          x="30" y="25" width="40" height="35" rx="8"
          fill="#1a1a1a"
          opacity="0.9"
        />

        <motion.ellipse
          cx="40" cy="40" rx="6" ry="8"
          fill="#3b82f6"
          animate={{ 
            scaleY: config.eyeScale,
            y: config.eyeY
          }}
          transition={{ duration: 0.3 }}
        >
          <animate attributeName="opacity" values="1;0;1" dur="3s" repeatCount="indefinite" />
        </motion.ellipse>

        <motion.ellipse
          cx="60" cy="40" rx="6" ry="8"
          fill="#3b82f6"
          animate={{ 
            scaleY: config.eyeScale,
            y: config.eyeY
          }}
          transition={{ duration: 0.3 }}
        >
          <animate attributeName="opacity" values="1;0;1" dur="3s" repeatCount="indefinite" />
        </motion.ellipse>

        <motion.path
          d={config.smilePath}
          stroke="#3b82f6"
          strokeWidth="2"
          fill="none"
          strokeLinecap="round"
          animate={{ d: config.smilePath }}
          transition={{ duration: 0.3 }}
        />

        <ellipse cx="35" cy="75" rx="8" ry="4" fill="#e8e8e8" opacity="0.6" />
        <ellipse cx="65" cy="75" rx="8" ry="4" fill="#e8e8e8" opacity="0.6" />
      </motion.svg>
    </motion.div>
  );
};

export default RobotAvatar;
