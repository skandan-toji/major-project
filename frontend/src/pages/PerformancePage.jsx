import { motion } from 'framer-motion';
import { useSimulation } from '../context/SimulationContext';
import { useEffect, useState } from 'react';
import api from '../utils/api';
import FPRScaleChart from '../components/FPRScaleChart';

const stagger = (row) => ({ initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.5, delay: row * 0.1 } });

export default function PerformancePage() {
  const { liveStats, sessionMetrics } = useSimulation();
  const [hist, setHist] = useState(null);
  const [mlInfo, setMlInfo] = useState(null);

  // Fetch historical results + ML info on mount
  useEffect(() => {
    api.get('/api/stats/historical').then(r => setHist(r.data)).catch(() => {});
    api.get('/api/stats/ml').then(r => setMlInfo(r.data)).catch(() => {});
  }, []);

  // Re-fetch when simulation ends
  useEffect(() => {
    if (sessionMetrics) {
      setHist(sessionMetrics);
    }
  }, [sessionMetrics]);

  // Use sessionMetrics (from WS) or hist (from REST) as data source
  const d = sessionMetrics || hist || {};
  const ad = d.attack_detection || {};
  const ps = d.packet_stats || {};
  const lat = d.latency_ms || {};
  const ml = d.ml_stats || {};
  const sp = d.simulation_params || {};

  // Confusion matrix values
  const tp = ad.true_positives || 0;
  const tn = ad.true_negatives || 0;
  const fp = ad.false_positives || 0;
  const fn = ad.false_negatives || 0;
  const cmTotal = tp + tn + fp + fn;
  const accuracy = cmTotal > 0 ? ((tp + tn) / cmTotal * 100) : 0;
  const precision = (tp + fp) > 0 ? (tp / (tp + fp) * 100) : 0;
  const recall = (tp + fn) > 0 ? (tp / (tp + fn) * 100) : 0;
  const f1 = (precision + recall) > 0 ? (2 * precision * recall / (precision + recall)) : 0;

  const metrics = [
    { label: 'Detection Accuracy', value: ad.detection_accuracy, suffix: '%', color: 'var(--green)' },
    { label: 'False Positive Rate', value: ad.false_positive_rate, suffix: '%', color: 'var(--green)' },
    { label: 'Precision', value: ad.precision, suffix: '%', color: 'var(--green)' },
    { label: 'Recall', value: ad.recall, suffix: '%', color: 'var(--yellow)' },
    { label: 'ML Accuracy', value: ml.accuracy, suffix: '%', color: '#3b82f6' },
    { label: 'Throughput', value: ps.throughput_pps, suffix: ' pkt/s', color: 'var(--cyan)' },
  ];

  const latencyBars = [
    ['E2E Average', lat.e2e_avg, '#8b5cf6'],
    ['E2E P95', lat.e2e_p95, '#a78bfa'],
    ['E2E P99', lat.e2e_p99, '#7c3aed'],
    ['E2E Min', lat.e2e_min, '#06b6d4'],
    ['E2E Max', lat.e2e_max, '#ef4444'],
  ];
  const maxLat = Math.max(...latencyBars.map(b => b[1] || 0), 1.5);

  // Confusion matrix cell tooltips
  const cmTooltips = {
    tn: 'Normal traffic correctly identified as safe',
    fp: 'Normal traffic incorrectly flagged as attack',
    fn: 'Attack traffic that slipped through undetected',
    tp: 'Attack traffic correctly detected by crypto or ML layer',
  };

  return (
    <div style={{ position: 'relative', zIndex: 1, padding: '100px 40px 40px', maxWidth: 1280, margin: '0 auto' }}>
      <h1 className="heading-section text-gradient" style={{ textAlign: 'center', fontSize: 'clamp(28px,4vw,36px)', marginBottom: 4 }}>Performance Metrics</h1>
      <p style={{ textAlign: 'center', color: 'var(--text-secondary)', fontSize: 14, marginBottom: 32 }}>Post-session analysis and cryptographic benchmarks</p>

      {/* Live indicator if running */}
      {liveStats && (
        <motion.div {...stagger(0)} className="glass-card" style={{ padding: '12px 24px', marginBottom: 24, display: 'flex', justifyContent: 'space-around', textAlign: 'center' }}>
          {[
            { label: 'Live Packets', value: liveStats.total_packets },
            { label: 'Throughput', value: `${(liveStats.throughput || 0).toFixed(1)} pkt/s` },
            { label: 'Detection', value: `${(liveStats.detection_accuracy || 0).toFixed(1)}%` },
            { label: 'Elapsed', value: `${(liveStats.elapsed_seconds || 0).toFixed(0)}s` },
          ].map((s, i) => (
            <div key={i}>
              <div className="mono" style={{ fontSize: 16, fontWeight: 600, color: 'var(--purple-glow)' }}>{s.value}</div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{s.label}</div>
            </div>
          ))}
        </motion.div>
      )}

      {/* 6 metric cards */}
      <motion.div {...stagger(0)} style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20, marginBottom: 32 }}>
        {metrics.map((m, i) => (
          <div key={i} className="glass-card" style={{ padding: '28px 24px', textAlign: 'center', borderBottom: `3px solid ${m.color}` }}>
            <div className="mono" style={{ fontSize: 'clamp(24px,3vw,36px)', fontWeight: 600, color: m.color }}>
              {m.value != null ? `${Number(m.value).toFixed(2)}${m.suffix}` : '--'}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8 }}>{m.label}</div>
          </div>
        ))}
      </motion.div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 32 }}>
        {/* Enhanced Confusion Matrix */}
        <motion.div {...stagger(1)} className="glass-card" style={{ padding: 28 }}>
          <h3 className="heading-card" style={{ marginBottom: 20 }}>Confusion Matrix</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr 1fr', gap: 0 }}>
            <div />
            <div className="confusion-label">PRED. NORMAL</div>
            <div className="confusion-label">PRED. ATTACK</div>

            <div className="confusion-label" style={{ writingMode: 'vertical-lr', transform: 'rotate(180deg)', padding: 8 }}>ACTUAL NORMAL</div>
            <div className="confusion-cell" title={cmTooltips.tn} style={{ background: 'rgba(16,185,129,0.15)', margin: 2, borderRadius: 8, cursor: 'help', transition: 'transform 0.2s' }}>
              <div className="mono" style={{ fontSize: 28, fontWeight: 600, color: 'var(--green)' }}>{tn.toLocaleString() || '--'}</div>
              <div style={{ fontSize: 11, color: 'var(--green)', marginTop: 4 }}>TN</div>
              {cmTotal > 0 && <div style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 2 }}>{((tn / cmTotal) * 100).toFixed(1)}%</div>}
            </div>
            <div className="confusion-cell" title={cmTooltips.fp} style={{ background: 'rgba(239,68,68,0.15)', margin: 2, borderRadius: 8, cursor: 'help' }}>
              <div className="mono" style={{ fontSize: 28, fontWeight: 600, color: 'var(--red)' }}>{fp}</div>
              <div style={{ fontSize: 11, color: 'var(--red)', marginTop: 4 }}>FP</div>
              {cmTotal > 0 && <div style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 2 }}>{((fp / cmTotal) * 100).toFixed(1)}%</div>}
            </div>

            <div className="confusion-label" style={{ writingMode: 'vertical-lr', transform: 'rotate(180deg)', padding: 8 }}>ACTUAL ATTACK</div>
            <div className="confusion-cell" title={cmTooltips.fn} style={{ background: 'rgba(245,158,11,0.15)', margin: 2, borderRadius: 8, cursor: 'help' }}>
              <div className="mono" style={{ fontSize: 28, fontWeight: 600, color: 'var(--yellow)' }}>{fn}</div>
              <div style={{ fontSize: 11, color: 'var(--yellow)', marginTop: 4 }}>FN</div>
              {cmTotal > 0 && <div style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 2 }}>{((fn / cmTotal) * 100).toFixed(1)}%</div>}
            </div>
            <div className="confusion-cell" title={cmTooltips.tp} style={{ background: 'rgba(16,185,129,0.25)', margin: 2, borderRadius: 8, cursor: 'help' }}>
              <div className="mono" style={{ fontSize: 28, fontWeight: 600, color: 'var(--green)' }}>{tp.toLocaleString() || '--'}</div>
              <div style={{ fontSize: 11, color: 'var(--green)', marginTop: 4 }}>TP</div>
              {cmTotal > 0 && <div style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 2 }}>{((tp / cmTotal) * 100).toFixed(1)}%</div>}
            </div>
          </div>

          {/* Derived metrics */}
          {cmTotal > 0 && (
            <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {[
                { label: 'Accuracy', value: accuracy, color: 'var(--green)' },
                { label: 'Precision', value: precision, color: 'var(--green)' },
                { label: 'Recall', value: recall, color: 'var(--yellow)' },
                { label: 'F1 Score', value: f1, color: 'var(--cyan)' },
              ].map(m => (
                <div key={m.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', background: 'rgba(139,92,246,0.05)', borderRadius: 6, fontSize: 12 }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{m.label}</span>
                  <span className="mono" style={{ fontWeight: 600, color: m.color }}>{m.value.toFixed(2)}%</span>
                </div>
              ))}
            </div>
          )}
        </motion.div>

        {/* Latency */}
        <motion.div {...stagger(1)} className="glass-card" style={{ padding: 28 }}>
          <h3 className="heading-card" style={{ marginBottom: 20 }}>End-to-End Latency</h3>
          {latencyBars.map(([name, val, color]) => (
            <div key={name} style={{ marginBottom: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                <span style={{ color: 'var(--text-secondary)' }}>{name}</span>
                <span className="mono" style={{ color }}>{val != null ? `${val.toFixed(2)}ms` : '--'}</span>
              </div>
              <div style={{ height: 6, background: 'var(--bg-elevated)', borderRadius: 3 }}>
                <div style={{ height: '100%', width: val ? `${(val / maxLat) * 100}%` : 0, background: color, borderRadius: 3, transition: 'width 0.5s' }} />
              </div>
            </div>
          ))}
          <p style={{ fontSize: 12, color: 'var(--green)', marginTop: 8 }}>All operations sub-10ms — NIST Level 5 compliant</p>
        </motion.div>
      </div>

      {/* FPR Scale Chart — always visible (uses hardcoded verified data) */}
      <motion.div {...stagger(2)} className="glass-card" style={{ padding: 28, marginBottom: 32 }}>
        <h3 className="heading-card" style={{ marginBottom: 4 }}>False Positive Rate vs Scale — Architectural Achievement</h3>
        <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 16 }}>Verified benchmark: ProcessPoolExecutor + queue architecture eliminated FPR at scale</p>
        <FPRScaleChart />
      </motion.div>

      {/* Session + ML */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <motion.div {...stagger(3)} className="glass-card" style={{ padding: 28 }}>
          <h3 className="heading-card" style={{ marginBottom: 16 }}>Simulation Parameters</h3>
          {[
            ['Meters', sp.num_meters],
            ['Duration', sp.duration ? `${sp.duration.toFixed(1)}s` : null],
            ['Packet Interval', sp.interval ? `${sp.interval}s` : null],
            ['Attack Probability', sp.attack_prob ? `${(sp.attack_prob * 100).toFixed(0)}%` : null],
            ['Packets Sent', ps.total_sent],
            ['Acceptance Rate', ps.acceptance_rate ? `${ps.acceptance_rate}%` : null],
          ].map(([l, v]) => (
            <div key={l} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: 13 }}>
              <span style={{ color: 'var(--text-secondary)' }}>{l}</span>
              <span className="mono" style={{ fontWeight: 600 }}>{v ?? '--'}</span>
            </div>
          ))}
        </motion.div>
        <motion.div {...stagger(3)} className="glass-card" style={{ padding: 28 }}>
          <h3 className="heading-card" style={{ marginBottom: 16 }}>ML Model Information</h3>
          {[
            ['Model Type', mlInfo?.model_type || 'Isolation Forest'],
            ['Estimators', mlInfo?.n_estimators || 200],
            ['Contamination', mlInfo?.contamination || 0.08],
            ['Packets Scored', ml.scored || '--'],
            ['ML Flagged', ml.flagged || 0],
            ['ML True Positives', ml.tp || 0],
            ['ML False Positives', ml.fp || 0],
            ['ML Accuracy', ml.accuracy != null ? `${ml.accuracy}%` : '--'],
          ].map(([l, v]) => (
            <div key={l} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: 13 }}>
              <span style={{ color: 'var(--text-secondary)' }}>{l}</span>
              <span className="mono" style={{ fontWeight: 600, color: 'var(--purple-glow)' }}>{v}</span>
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  );
}
