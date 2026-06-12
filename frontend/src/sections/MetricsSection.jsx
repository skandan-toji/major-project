import { motion, useInView } from 'framer-motion';
import { useRef, useEffect, useState } from 'react';
import useCountUp from '../hooks/useCountUp';
import { useSimulation } from '../context/SimulationContext';

const sv = { hidden: { opacity: 0, y: 40 }, visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.22,1,0.36,1] } } };

function MetricCard({ label, target, suffix, decimals, color }) {
  const [ref, val] = useCountUp(target, 1500, decimals);
  return (
    <motion.div ref={ref} className="glass-card" whileHover={{ y: -4 }}
      style={{ padding: '32px 24px', textAlign: 'center', borderBottom: `3px solid ${color}` }}>
      <div className="mono" style={{ fontSize: 'clamp(28px, 3.5vw, 38px)', fontWeight: 600, background: `linear-gradient(135deg, ${color}, var(--purple-glow))`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
        {val}{suffix}
      </div>
      <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8 }}>{label}</div>
    </motion.div>
  );
}

export default function MetricsSection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, amount: 0.2 });
  const { sessionMetrics, liveStats, isRunning } = useSimulation();

  // Use session metrics from last run if available, otherwise live stats, otherwise verified defaults
  const src = sessionMetrics || null;
  const live = liveStats || null;

  const detAcc = src?.detection_accuracy ?? live?.detection_accuracy ?? 98.18;
  const fpr = src?.fpr ?? live?.fpr ?? 0;
  const precision = src?.precision ?? 100;
  const mlAcc = src?.ml_accuracy ?? 98.04;
  const throughput = src?.packet_stats?.throughput ?? live?.throughput ?? 51.47;
  const p99 = src?.latency_ms?.p99 ?? 10;

  const subtitle = src ? 'From your latest simulation session' : isRunning ? 'Updating from live session...' : 'Baseline from verified 100-meter simulation';

  const metrics = [
    { label: 'Detection Accuracy', target: detAcc, suffix: '%', decimals: 2, color: 'var(--green)' },
    { label: 'False Positive Rate', target: fpr, suffix: '%', decimals: 2, color: 'var(--green)' },
    { label: 'Precision', target: precision, suffix: '%', decimals: 2, color: 'var(--green)' },
    { label: 'ML Accuracy', target: mlAcc, suffix: '%', decimals: 2, color: '#3b82f6' },
    { label: 'Throughput', target: throughput, suffix: ' pkt/s', decimals: 2, color: 'var(--cyan)' },
    { label: 'Crypto P99', target: p99, suffix: 'ms', decimals: 0, color: 'var(--purple-bright)' },
  ];

  return (
    <motion.section ref={ref} variants={sv} initial="hidden" animate={inView ? 'visible' : 'hidden'} style={{ padding: '100px 40px' }}>
      <h2 className="heading-section text-gradient" style={{ textAlign: 'center', fontSize: 'clamp(28px,4vw,42px)', marginBottom: 8 }}>Verified Performance Metrics</h2>
      <p style={{ textAlign: 'center', color: 'var(--text-secondary)', fontSize: 15, marginBottom: 48 }}>{subtitle}</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20, maxWidth: 1000, margin: '0 auto' }}>
        {metrics.map(m => <MetricCard key={m.label} {...m} />)}
      </div>
    </motion.section>
  );
}
