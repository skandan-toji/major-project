import { motion } from 'framer-motion';

const stages = [
  { key: 'total', label: 'Total Attacks Injected', sublabel: 'All attacks enter here', color: '#94a3b8' },
  { key: 'after_hmac', label: 'After HMAC Check', sublabel: 'Caught by HMAC', caughtKey: 'caught_hmac', color: '#8b5cf6' },
  { key: 'after_seq', label: 'After Sequence Check', sublabel: 'Caught by Sequence', caughtKey: 'caught_seq', color: '#3b82f6' },
  { key: 'after_ts', label: 'After Timestamp Check', sublabel: 'Caught by Timestamp', caughtKey: 'caught_ts', color: '#06b6d4' },
  { key: 'after_ml', label: 'After ML Layer', sublabel: 'Caught by ML', caughtKey: 'caught_ml', color: '#10b981' },
  { key: 'missed', label: 'Missed (False Negatives)', sublabel: 'Slipped through all layers', color: '#ef4444' },
];

export default function AttackSurvivalChart({ data = {} }) {
  const total = data.total || 0;
  if (total === 0) {
    return (
      <div style={{ textAlign: 'center', padding: 40, color: '#5a5a78', fontSize: 13 }}>
        Waiting for attack data...
      </div>
    );
  }

  const hmac = data.caught_hmac || 0;
  const seq = data.caught_seq || 0;
  const ts = data.caught_ts || 0;
  const ml = data.caught_ml || 0;
  const missed = data.missed || 0;

  const survivals = [
    total,
    total - hmac,
    total - hmac - seq,
    total - hmac - seq - ts,
    total - hmac - seq - ts - ml,
    missed,
  ];

  const caughtCounts = [0, hmac, seq, ts, ml, 0];
  const totalCaught = hmac + seq + ts + ml;
  const catchRate = total > 0 ? ((totalCaught / total) * 100).toFixed(2) : '0.00';

  return (
    <div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {stages.map((stage, i) => {
          const survive = Math.max(0, survivals[i]);
          const pct = total > 0 ? ((survive / total) * 100) : 0;
          const widthPct = total > 0 ? Math.max(4, (survive / total) * 100) : 4;
          const caught = caughtCounts[i];

          return (
            <motion.div
              key={stage.key}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.08, duration: 0.4 }}
              style={{ display: 'flex', alignItems: 'center', gap: 12 }}
            >
              <div style={{ flex: 1 }}>
                <div
                  style={{
                    height: 28,
                    width: `${widthPct}%`,
                    background: `linear-gradient(90deg, ${stage.color}, ${stage.color}88)`,
                    borderRadius: 4,
                    display: 'flex',
                    alignItems: 'center',
                    paddingLeft: 8,
                    transition: 'width 0.8s ease',
                    minWidth: 40,
                  }}
                >
                  <span className="mono" style={{ fontSize: 11, fontWeight: 600, color: 'white', whiteSpace: 'nowrap' }}>
                    {survive} ({pct.toFixed(1)}%)
                  </span>
                </div>
              </div>
              <div style={{ width: 180, flexShrink: 0 }}>
                <div style={{ fontSize: 11, color: 'var(--text-primary)', fontWeight: 500 }}>{stage.label}</div>
                {caught > 0 && (
                  <div style={{ fontSize: 9, color: stage.color }}>
                    ↳ {stage.sublabel}: {caught}
                  </div>
                )}
                {i === 0 && <div style={{ fontSize: 9, color: '#5a5a78' }}>{stage.sublabel}</div>}
                {i === stages.length - 1 && <div style={{ fontSize: 9, color: '#ef4444' }}>{stage.sublabel}</div>}
              </div>
            </motion.div>
          );
        })}
      </div>
      {/* Connecting arrows */}
      <div style={{ textAlign: 'center', marginTop: 12, fontSize: 12, color: '#10b981', fontWeight: 600 }}>
        Multi-layer defense catches {catchRate}% of all attack attempts
      </div>
    </div>
  );
}
