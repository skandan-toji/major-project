import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import api from '../utils/api';

const defaultNodes = [
  { icon: '🔏', name: 'Dilithium5', desc: 'Digital signatures', metric: '--', std: 'NIST PQC' },
  { icon: '🔐', name: 'Kyber1024', desc: 'Key encapsulation', metric: '--', std: 'NIST PQC' },
  { icon: '🛡️', name: 'AES-256-GCM', desc: 'Encryption', metric: '--', std: 'FIPS 197' },
  { icon: '🔑', name: 'HMAC-SHA256', desc: 'Auth codes', metric: '--', std: 'RFC 2104' },
  { icon: '🔢', name: 'Seq+Timestamp', desc: 'Replay guard', metric: '--', std: 'Custom' },
  { icon: '📋', name: 'Session Mgmt', desc: 'Lifecycle', metric: '--', std: 'Custom' },
  { icon: '🤖', name: 'Isolation Forest', desc: 'ML detection', metric: '--', std: 'scikit-learn' },
];

const techStack = [
  { icon: '🐍', name: 'Python', desc: 'Backend runtime' },
  { icon: '⚡', name: 'FastAPI', desc: 'REST + WebSocket' },
  { icon: '⚛️', name: 'React 18', desc: 'Frontend UI' },
  { icon: '📊', name: 'Recharts', desc: 'Visualization' },
  { icon: '🔐', name: 'pqcrypto', desc: 'Post-quantum crypto' },
  { icon: '🤖', name: 'scikit-learn', desc: 'ML detection' },
];

const decisions = [
  { title: 'Why Dilithium5 over lower variants?', desc: 'Dilithium5 provides NIST Level 5 security (equivalent to AES-256). While Dilithium2/3 are faster, Level 5 ensures quantum resilience against future cryptanalytic advances.' },
  { title: 'Why ML scores before crypto?', desc: 'Attack packets with anomalous features (seq_delta < 0 for replay, hmac_valid=0 for MITM) are scored while those features are still visible. After crypto rejects them, the features are lost.' },
  { title: 'Why per-meter queues?', desc: 'Each meter gets its own async queue in the Control Center. This prevents a slow or misbehaving meter from blocking others, ensuring fair throughput distribution.' },
  { title: 'Why ProcessPoolExecutor?', desc: 'Dilithium5 sign/verify and Kyber1024 encrypt/decrypt are CPU-intensive PQC operations. Offloading them to separate processes prevents blocking the asyncio event loop.' },
];

export default function SystemInfoPage() {
  const [sysInfo, setSysInfo] = useState(null);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    api.get('/api/metrics/system').then(r => setSysInfo(r.data)).catch(() => {});
    api.get('/api/health').then(r => setHealth(r.data)).catch(() => {});
  }, []);

  const si = sysInfo || {};
  const ks = si.key_sizes || {};

  // Build params from API data
  const params = [
    ['NIST Security Level', si.security_level || '--', 'NIST PQC'],
    ['Dilithium Variant', si.dilithium_variant || '--', 'NIST PQC'],
    ['Kyber Variant', si.kyber_variant || '--', 'NIST PQC'],
    ['AES Mode', si.aes_mode || '--', 'FIPS 197'],
    ['HMAC Algorithm', si.hmac_algorithm || '--', 'RFC 2104'],
    ['Session Lifetime', si.session_lifetime ? `${si.session_lifetime} seconds` : '--', 'Custom'],
    ['Timestamp Window', si.timestamp_window ? `${si.timestamp_window} seconds` : '--', 'Custom'],
    ['Dilithium5 Public Key', ks.dilithium5_public ? `${ks.dilithium5_public} bytes` : '--', '--'],
    ['Dilithium5 Signature', ks.dilithium5_signature ? `${ks.dilithium5_signature} bytes` : '--', '--'],
    ['Kyber1024 Public Key', ks.kyber1024_public ? `${ks.kyber1024_public} bytes` : '--', '--'],
    ['AES Key Size', ks.aes_key ? `${ks.aes_key} bits` : '--', '--'],
    ['HMAC Output', ks.hmac_output ? `${ks.hmac_output} bits` : '--', '--'],
    ['ML Model', si.ml_model || '--', 'scikit-learn'],
    ['ML Estimators', si.ml_estimators || '--', '--'],
    ['ML Contamination', si.ml_contamination || '--', '--'],
    ['Max Meters', si.max_meters || '--', '--'],
  ];

  // Build pipeline nodes with real timing from API
  const nodes = [...defaultNodes];
  if (si.session_lifetime) nodes[5].metric = `${si.session_lifetime}s`;
  if (si.timestamp_window) nodes[4].metric = `${si.timestamp_window}s`;

  return (
    <div style={{ position: 'relative', zIndex: 1, padding: '100px 40px 60px', maxWidth: 1280, margin: '0 auto' }}>
      <h1 className="heading-section text-gradient" style={{ textAlign: 'center', fontSize: 'clamp(28px,4vw,36px)', marginBottom: 4 }}>System Information</h1>
      <p style={{ textAlign: 'center', color: 'var(--text-secondary)', fontSize: 14, marginBottom: 40 }}>Architecture, parameters, and design decisions</p>

      {/* API Health Status */}
      {health && (
        <div className="glass-card" style={{ padding: '16px 24px', marginBottom: 24, display: 'flex', justifyContent: 'space-around', textAlign: 'center' }}>
          {Object.entries(health.modules || {}).map(([mod, status]) => (
            <div key={mod} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: status === 'loaded' || status === 'ready' ? 'var(--green)' : status === 'running' ? 'var(--cyan)' : 'var(--yellow)' }} />
              <span style={{ fontSize: 13, textTransform: 'capitalize' }}>{mod}</span>
              <span className="badge badge-green" style={{ fontSize: 9 }}>{status}</span>
            </div>
          ))}
        </div>
      )}

      {/* Pipeline */}
      <div className="glass-card" style={{ padding: 28, marginBottom: 32 }}>
        <h3 className="heading-card text-gradient" style={{ textAlign: 'center', marginBottom: 24 }}>Security Architecture Pipeline</h3>
        <div style={{ display: 'flex', alignItems: 'center', overflowX: 'auto', gap: 0, padding: '10px 0' }}>
          {nodes.map((n, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center' }}>
              <motion.div className="glass-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}
                style={{ width: 130, minHeight: 160, padding: '16px 12px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
                <div style={{ fontSize: 24, marginBottom: 6 }}>{n.icon}</div>
                <div style={{ fontFamily: "'Sora', sans-serif", fontWeight: 600, fontSize: 12 }}>{n.name}</div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 8 }}>{n.desc}</div>
                <span className="badge badge-purple" style={{ fontSize: 9, marginTop: 'auto' }}>{n.metric}</span>
              </motion.div>
              {i < nodes.length - 1 && (
                <svg width="30" height="20" style={{ flexShrink: 0 }}>
                  <line x1="0" y1="10" x2="30" y2="10" stroke="rgba(124,58,237,0.4)" strokeWidth="1" />
                  <circle r="2.5" fill="#7c3aed"><animateMotion dur="1.5s" repeatCount="indefinite" path="M 0,10 L 30,10" /></circle>
                </svg>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Params table */}
      <div className="glass-card" style={{ padding: 28, marginBottom: 32 }}>
        <h3 className="heading-card text-gradient" style={{ marginBottom: 16 }}>Security Parameters</h3>
        <table className="feed-table">
          <thead><tr><th>Parameter</th><th>Value</th><th>Standard</th></tr></thead>
          <tbody>
            {params.map(([p, v, s], i) => (
              <tr key={i} style={{ background: i % 2 === 0 ? 'rgba(255,255,255,0.01)' : 'transparent' }}>
                <td style={{ color: 'var(--text-secondary)' }}>{p}</td>
                <td style={{ fontWeight: 600 }}>{v}</td>
                <td><span className={s.startsWith('NIST') ? 'badge badge-purple' : s.startsWith('RFC') ? 'badge badge-green' : s === 'scikit-learn' ? 'badge badge-blue' : 'badge badge-blue'}>{s}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Tech Stack */}
      <h3 className="heading-card text-gradient" style={{ textAlign: 'center', marginBottom: 16 }}>Tech Stack</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 16, marginBottom: 32 }}>
        {techStack.map((t, i) => (
          <motion.div key={i} className="glass-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}
            style={{ padding: 20, textAlign: 'center' }}>
            <div style={{ fontSize: 28, marginBottom: 8 }}>{t.icon}</div>
            <div style={{ fontFamily: "'Sora', sans-serif", fontWeight: 600, fontSize: 13 }}>{t.name}</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{t.desc}</div>
          </motion.div>
        ))}
      </div>

      {/* Design Decisions */}
      <h3 className="heading-card text-gradient" style={{ textAlign: 'center', marginBottom: 16 }}>Key Design Decisions</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 20 }}>
        {decisions.map((d, i) => (
          <div key={i} className="glass-card glass-card-purple" style={{ padding: 24 }}>
            <h4 style={{ fontFamily: "'Sora', sans-serif", fontWeight: 600, fontSize: 14, color: 'var(--purple-glow)', marginBottom: 8 }}>{d.title}</h4>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{d.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
