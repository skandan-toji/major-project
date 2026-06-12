import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

export default function StatCard({ value, label, color = 'var(--purple-light)', suffix = '', decimals = 0, delay = 0 }) {
  const [display, setDisplay] = useState(0);
  const numVal = typeof value === 'number' ? value : parseFloat(value) || 0;

  useEffect(() => {
    if (numVal === 0) { setDisplay(0); return; }
    let start = 0;
    const duration = 1200;
    const startTime = performance.now();
    const animate = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(start + (numVal - start) * eased);
      if (progress < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [numVal]);

  return (
    <motion.div
      className="glass-card stat-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <div className="stat-value gradient-text">
        {decimals > 0 ? display.toFixed(decimals) : Math.round(display).toLocaleString()}{suffix}
      </div>
      <div className="stat-label">{label}</div>
    </motion.div>
  );
}
