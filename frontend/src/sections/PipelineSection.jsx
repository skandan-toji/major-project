import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';

const sv = { hidden: { opacity: 0, y: 40 }, visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.22,1,0.36,1] } } };

const nodes = [
  { icon: '🔏', name: 'Dilithium5', desc: 'Digital signatures', metric: '0.73ms sign' },
  { icon: '🔐', name: 'Kyber1024', desc: 'Key encapsulation', metric: '0.17ms enc' },
  { icon: '🛡️', name: 'AES-256-GCM', desc: 'Authenticated encryption', metric: '1.15ms enc' },
  { icon: '🔑', name: 'HMAC-SHA256', desc: 'Message authentication', metric: '~0.03ms' },
  { icon: '🔢', name: 'Seq+Timestamp', desc: 'Replay prevention', metric: '30s window' },
  { icon: '📋', name: 'Session Mgmt', desc: 'Lifecycle control', metric: '900s life' },
  { icon: '🤖', name: 'Isolation Forest', desc: 'ML anomaly detection', metric: '98.04%' },
];

function Connector() {
  return (
    <svg width="40" height="20" style={{ flexShrink: 0 }}>
      <line x1="0" y1="10" x2="40" y2="10" stroke="rgba(124,58,237,0.4)" strokeWidth="1" />
      <circle r="3" fill="#7c3aed">
        <animateMotion dur="1.5s" repeatCount="indefinite" path="M 0,10 L 40,10" />
      </circle>
    </svg>
  );
}

export default function PipelineSection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, amount: 0.2 });
  return (
    <motion.section ref={ref} variants={sv} initial="hidden" animate={inView ? 'visible' : 'hidden'}
      style={{ padding: '100px 40px', background: 'linear-gradient(180deg, transparent, rgba(124,58,237,0.03), transparent)' }}>
      <h2 className="heading-section text-gradient" style={{ textAlign: 'center', fontSize: 'clamp(28px,4vw,40px)', marginBottom: 8 }}>7-Layer Defense Pipeline</h2>
      <p style={{ textAlign: 'center', color: 'var(--text-secondary)', fontSize: 15, marginBottom: 48 }}>Every packet survives all 7 checks or gets dropped</p>
      <div style={{ display: 'flex', alignItems: 'center', maxWidth: 1200, margin: '0 auto', overflowX: 'auto', padding: '20px 20px 30px', gap: 0 }}>
        {nodes.map((n, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center' }}>
            <motion.div className="glass-card" initial={{ opacity: 0, y: 20 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ delay: i * 0.1 }}
              style={{ width: 140, minHeight: 170, display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '20px 14px', textAlign: 'center', flexShrink: 0 }}>
              <div style={{ fontSize: 28, marginBottom: 8 }}>{n.icon}</div>
              <div style={{ fontFamily: "'Sora', sans-serif", fontWeight: 600, fontSize: 13, marginBottom: 4 }}>{n.name}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 12, lineHeight: 1.3 }}>{n.desc}</div>
              <span className="badge badge-purple" style={{ fontSize: 9, marginTop: 'auto' }}>{n.metric}</span>
            </motion.div>
            {i < nodes.length - 1 && <Connector />}
          </div>
        ))}
      </div>
    </motion.section>
  );
}
