import { motion } from 'framer-motion';

export default function GlassCard({ children, className = '', glow, delay = 0, ...props }) {
  const glowStyle = glow ? { borderColor: glow, boxShadow: `0 0 20px ${glow}22, 0 20px 40px rgba(0,0,0,0.4)` } : {};
  return (
    <motion.div
      className={`glass-card ${className}`}
      style={glowStyle}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      {...props}
    >
      {children}
    </motion.div>
  );
}
