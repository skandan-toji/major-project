import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';

const sv = { hidden: { opacity: 0, y: 40 }, visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.22,1,0.36,1] } } };

export default function CTASection({ onStart, goLive }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, amount: 0.3 });
  return (
    <motion.section ref={ref} variants={sv} initial="hidden" animate={inView ? 'visible' : 'hidden'}
      style={{ padding: '120px 40px', textAlign: 'center', background: 'linear-gradient(180deg, transparent, rgba(124,58,237,0.07), transparent)', position: 'relative' }}>
      {/* Circuit-node icon */}
      <div style={{ margin: '0 auto 24px', width: 80, height: 80, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
          <path d="M12 3 L21 18 L3 18 Z" stroke="url(#ctaGrad)" strokeWidth="1.2" fill="none" opacity="0.5" />
          <circle cx="12" cy="3" r="2.5" fill="#a78bfa" /><circle cx="21" cy="18" r="2.5" fill="#7c3aed" /><circle cx="3" cy="18" r="2.5" fill="#60a5fa" />
          <circle cx="12" cy="12" r="2.5" fill="url(#ctaGrad)" />
          <circle cx="12" cy="12" r="5" stroke="#a78bfa" strokeWidth="0.5" fill="none" opacity="0.3">
            <animate attributeName="r" values="5;8;5" dur="3s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.3;0.08;0.3" dur="3s" repeatCount="indefinite" />
          </circle>
          <defs><linearGradient id="ctaGrad" x1="0" y1="0" x2="24" y2="24"><stop offset="0%" stopColor="#a78bfa" /><stop offset="100%" stopColor="#60a5fa" /></linearGradient></defs>
        </svg>
      </div>
      <h2 className="heading-hero" style={{ fontSize: 'clamp(32px,5vw,52px)', marginBottom: 16 }}>
        Defend Your Grid.<br />
        <span className="text-gradient-warm">Starting Now.</span>
      </h2>
      <p style={{ color: 'var(--text-secondary)', fontSize: 15, maxWidth: 420, margin: '0 auto 36px' }}>
        Quantum-resilient encryption. Real-time threat detection. Zero false positives.
      </p>
      <div style={{ display: 'flex', gap: 16, justifyContent: 'center' }}>
        <button className="btn-primary" onClick={onStart}>Start Simulation</button>
        <button className="btn-ghost" onClick={goLive}>View Architecture</button>
      </div>
      <div style={{ display: 'flex', gap: 20, justifyContent: 'center', marginTop: 32 }}>
        {['✓ No real hardware needed', '✓ NIST Level 5 Security', '✓ Open simulation'].map(t => (
          <span key={t} className="glass-card" style={{ padding: '6px 14px', fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', borderRadius: 100 }}>{t}</span>
        ))}
      </div>
    </motion.section>
  );
}
