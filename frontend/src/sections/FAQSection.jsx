import { useState } from 'react';
import { motion, AnimatePresence, useInView } from 'framer-motion';
import { useRef } from 'react';

const sv = { hidden: { opacity: 0, y: 40 }, visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.22,1,0.36,1] } } };

const faqs = [
  { q: 'What is this security framework?', a: 'A hybrid quantum-resilient security framework that combines post-quantum cryptography (Dilithium5 + Kyber1024) with machine learning anomaly detection to protect smart grid communication from Man-in-the-Middle attacks, even against future quantum computers.' },
  { q: 'Why post-quantum cryptography?', a: 'Quantum computers will break RSA and ECC. Dilithium5 and Kyber1024 are NIST-standardized lattice-based algorithms that are mathematically resistant to quantum attacks, providing long-term security at NIST Level 5 (AES-256 equivalent).' },
  { q: 'How does attack detection work?', a: 'An Isolation Forest ML model trained on 12,000 traffic samples scores every incoming packet. The crypto layers (HMAC, sequence numbers, timestamps) act as the primary defense, while ML catches behavioral anomalies the crypto layers cannot see.' },
  { q: 'What attacks does the system detect?', a: 'Replay attacks (via sequence numbers + timestamps), MITM tampering (via HMAC-SHA256 verification), flood attacks (via ML packet rate analysis), and impersonation attempts (via Dilithium5 signature verification).' },
  { q: 'What scale does the simulation support?', a: '10 to 500 concurrent smart meters on a single machine. Measured throughput is 51.47 packets/second with sub-10ms crypto latency at NIST Level 5 security. All meters operate asynchronously with per-meter packet queues.' },
];

function FAQItem({ q, a }) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{ borderBottom: '1px solid var(--border-subtle)' }}>
      <button onClick={() => setOpen(!open)} style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 0', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-primary)', fontFamily: "'Inter', sans-serif", fontSize: 15, fontWeight: 500, textAlign: 'left' }}>
        {q}
        <span style={{ fontSize: 18, color: 'var(--purple-glow)', flexShrink: 0, marginLeft: 16 }}>{open ? '−' : '+'}</span>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3 }}>
            <p style={{ paddingBottom: 16, fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.65 }}>{a}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function FAQSection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, amount: 0.2 });
  return (
    <motion.section ref={ref} variants={sv} initial="hidden" animate={inView ? 'visible' : 'hidden'} style={{ padding: '80px 40px' }}>
      <h2 className="heading-section" style={{ textAlign: 'center', fontSize: 'clamp(28px,4vw,42px)', marginBottom: 8, color: 'white' }}>Frequently Asked Questions</h2>
      <p style={{ textAlign: 'center', fontSize: 14, color: 'var(--text-secondary)', marginBottom: 40 }}>Have a question? <span style={{ color: 'var(--purple-glow)', textDecoration: 'underline', cursor: 'pointer' }}>Contact us</span></p>
      <div style={{ maxWidth: 680, margin: '0 auto' }}>
        {faqs.map((f, i) => <FAQItem key={i} {...f} />)}
      </div>
    </motion.section>
  );
}
