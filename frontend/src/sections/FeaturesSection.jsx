import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';

const sv = { hidden: { opacity: 0, y: 40 }, visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.22,1,0.36,1] } } };

function Feature({ badge, title, body, metric, metricColor, visual, reverse }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, amount: 0.3 });
  return (
    <motion.div ref={ref} variants={sv} initial="hidden" animate={inView ? 'visible' : 'hidden'} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 60, alignItems: 'center', padding: '100px 0', maxWidth: 1100, margin: '0 auto', direction: reverse ? 'rtl' : 'ltr' }}>
      <div style={{ direction: 'ltr' }}>
        <span className="badge badge-purple" style={{ marginBottom: 12, display: 'inline-block' }}>{badge}</span>
        <h2 className="heading-section text-gradient" style={{ fontSize: 'clamp(28px, 4vw, 42px)', marginBottom: 16 }}>{title}</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: 15, lineHeight: 1.7, marginBottom: 20 }}>{body}</p>
        <span className="glass-card" style={{ display: 'inline-block', padding: '8px 16px', fontSize: 12, fontFamily: "'JetBrains Mono', monospace", color: metricColor || 'var(--green)', borderColor: `${metricColor || 'var(--green)'}33` }}>{metric}</span>
      </div>
      <div style={{ direction: 'ltr' }}>{visual}</div>
    </motion.div>
  );
}

function LatencyBars() {
  const bars = [['Dil5 Sign', 0.73, 73], ['Dil5 Verify', 0.23, 23], ['Kyber Enc', 0.17, 17], ['AES Enc', 1.15, 100], ['AES Dec', 0.08, 8], ['HMAC', 0.03, 3]];
  return (
    <div className="glass-card" style={{ padding: 28 }}>
      {bars.map(([name, val, w]) => (
        <div key={name} style={{ marginBottom: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 4 }}>
            <span style={{ color: 'var(--text-secondary)' }}>{name}</span>
            <span className="mono" style={{ color: 'var(--purple-glow)' }}>{val}ms</span>
          </div>
          <div style={{ height: 6, background: 'var(--bg-elevated)', borderRadius: 3 }}>
            <div style={{ height: '100%', width: `${w}%`, background: 'linear-gradient(90deg, var(--purple-core), var(--blue-core))', borderRadius: 3 }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function AttackLogMini() {
  const rows = [['Replay Attack', 'badge-red', 'SEQ NO'], ['MITM Tamper', 'badge-blue', 'HMAC'], ['Flood Attack', 'badge-red', 'ML MODEL']];
  return (
    <div className="glass-card" style={{ padding: 28 }}>
      {rows.map(([name, cls, method], i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 0', borderBottom: i < 2 ? '1px solid var(--border-subtle)' : 'none' }}>
          <span className={`badge ${cls}`}>{name}</span>
          <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{method}</span>
          <span style={{ fontSize: 11, color: 'var(--green)', fontWeight: 600 }}>BLOCKED</span>
        </div>
      ))}
    </div>
  );
}

function SessionTimeline() {
  const sessions = [['SM_014', 85], ['SM_027', 62], ['SM_003', 41]];
  return (
    <div className="glass-card" style={{ padding: 28 }}>
      {sessions.map(([id, pct], i) => (
        <div key={i} style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <span style={{ fontFamily: "'Sora', sans-serif", fontWeight: 600, fontSize: 13 }}>{id}</span>
            <span className="badge badge-green">Active</span>
          </div>
          <div style={{ height: 4, background: 'var(--bg-elevated)', borderRadius: 2 }}>
            <div style={{ height: '100%', width: `${pct}%`, background: 'linear-gradient(90deg, var(--purple-core), var(--purple-bright))', borderRadius: 2, transition: 'width 1s ease' }} />
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 3 }}>{Math.round(pct * 9)}s remaining</div>
        </div>
      ))}
    </div>
  );
}

export default function FeaturesSection() {
  return (
    <section style={{ padding: '0 40px' }}>
      <Feature badge="Layer 1–2" title="Detailed Cryptographic Analysis"
        body="Every packet authenticated with Dilithium5 lattice-based signatures and session keys protected by Kyber1024 key encapsulation — quantum resistant at NIST Level 5."
        metric="Sign: 0.73ms  |  Verify: 0.23ms" metricColor="var(--green)" visual={<LatencyBars />} />
      <Feature badge="ML Detection" title="Real-Time Attack Detection" reverse
        body="Isolation Forest ML model trained on 12,000 traffic samples scores every packet before cryptographic verification. Zero false positives in verified testing."
        metric="98.18% Detection Accuracy" metricColor="var(--green)" visual={<AttackLogMini />} />
      <Feature badge="Session Layer" title="Live Session Management"
        body="Full session lifecycle — Dilithium5 authentication, Kyber1024 key exchange, 15-minute session windows, automatic expiry and re-authentication — all monitored in real time."
        metric="900s Session Lifetime" metricColor="var(--purple-glow)" visual={<SessionTimeline />} />
    </section>
  );
}
