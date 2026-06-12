import { motion } from 'framer-motion';
import { useSimulation } from '../context/SimulationContext';
import DualLayerComparisonChart from '../components/DualLayerComparisonChart';
import ErrorRateChart from '../components/ErrorRateChart';
import FPRScaleChart from '../components/FPRScaleChart';
import MLCalibrationChart from '../components/MLCalibrationChart';
import AttackSurvivalChart from '../components/AttackSurvivalChart';
import CumulativePerformanceChart from '../components/CumulativePerformanceChart';
import LatencyDistributionChart from '../components/LatencyDistributionChart';
import MeterHealthHeatmap from '../components/MeterHealthHeatmap';

const stagger = (row) => ({ initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.5, delay: row * 0.1 } });

export default function AnalyticsPage() {
  const {
    liveStats, startTime, isRunning, numMeters,
    dualLayerData, errorRateData, calibrationData,
    cumulativeData, meterHealth, survivalData,
  } = useSimulation();

  const elapsed = startTime ? Math.floor((Date.now() - startTime.getTime()) / 1000) : 0;
  const elapsedStr = `${Math.floor(elapsed / 60)}:${String(elapsed % 60).padStart(2, '0')}`;

  return (
    <div style={{ position: 'relative', zIndex: 1, padding: '100px 40px 40px', maxWidth: 1360, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 28 }}>
        <div>
          <h1 className="heading-section text-gradient" style={{ fontSize: 'clamp(28px,4vw,36px)', marginBottom: 4 }}>Real-Time Analytics</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Live performance metrics — updated per packet</p>
        </div>
        {isRunning && (
          <div className="glass-card" style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--green)', animation: 'live-pulse 2s ease-in-out infinite' }} />
            <span className="mono" style={{ fontSize: 13, color: 'var(--text-primary)' }}>Session: {elapsedStr}</span>
          </div>
        )}
      </div>

      {/* Live summary bar */}
      {liveStats && (
        <motion.div {...stagger(0)} className="glass-card" style={{ padding: '14px 24px', marginBottom: 20, display: 'flex', justifyContent: 'space-around', textAlign: 'center' }}>
          {[
            { label: 'Total Packets', value: liveStats.total_packets, color: 'var(--text-primary)' },
            { label: 'Accepted', value: liveStats.accepted, color: 'var(--green)' },
            { label: 'Rejected', value: liveStats.rejected, color: 'var(--red)' },
            { label: 'Detection', value: `${(liveStats.detection_accuracy || 0).toFixed(1)}%`, color: 'var(--green)' },
            { label: 'FPR', value: `${(liveStats.fpr || 0).toFixed(2)}%`, color: 'var(--cyan)' },
            { label: 'Throughput', value: `${(liveStats.throughput || 0).toFixed(1)} pkt/s`, color: 'var(--purple-glow)' },
          ].map((s, i) => (
            <div key={i}>
              <div className="mono" style={{ fontSize: 16, fontWeight: 600, color: s.color }}>{s.value}</div>
              <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginTop: 2 }}>{s.label}</div>
            </div>
          ))}
        </motion.div>
      )}

      {/* ROW 1 — Dual Layer Comparison (full width) */}
      <motion.div {...stagger(0)} className="glass-card" style={{ padding: 24, marginBottom: 20 }}>
        <h3 style={{ fontFamily: "'Sora', sans-serif", fontWeight: 600, fontSize: 14, marginBottom: 4 }}>Dual-Shield Detection Layer Comparison</h3>
        <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 16 }}>Cryptographic vs ML behavioral detection</p>
        <DualLayerComparisonChart data={dualLayerData} liveStats={liveStats} />
      </motion.div>

      {/* ROW 2 — Error Rate + FPR Scale (50/50) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        <motion.div {...stagger(1)} className="glass-card" style={{ padding: 24 }}>
          <h3 style={{ fontFamily: "'Sora', sans-serif", fontWeight: 600, fontSize: 14, marginBottom: 4 }}>Error Rate vs Attack Intensity</h3>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 16 }}>Analogous to Quantum Bit Error Rate (QBER) analysis</p>
          <ErrorRateChart data={errorRateData} />
        </motion.div>
        <motion.div {...stagger(1)} className="glass-card" style={{ padding: 24 }}>
          <h3 style={{ fontFamily: "'Sora', sans-serif", fontWeight: 600, fontSize: 14, marginBottom: 4 }}>False Positive Rate vs Scale</h3>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 16 }}>Architecture fix impact: 82% FPR → 0% FPR at scale</p>
          <FPRScaleChart />
        </motion.div>
      </div>

      {/* ROW 3 — Attack Survival + ML Calibration (60/40) */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: 20, marginBottom: 20 }}>
        <motion.div {...stagger(2)} className="glass-card" style={{ padding: 24 }}>
          <h3 style={{ fontFamily: "'Sora', sans-serif", fontWeight: 600, fontSize: 14, marginBottom: 4 }}>Attack Survival Rate — Defense in Depth</h3>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 16 }}>Attacks eliminated at each security layer</p>
          <AttackSurvivalChart data={survivalData} />
        </motion.div>
        <motion.div {...stagger(2)} className="glass-card" style={{ padding: 24 }}>
          <h3 style={{ fontFamily: "'Sora', sans-serif", fontWeight: 600, fontSize: 14, marginBottom: 4 }}>ML Online Threshold Calibration</h3>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 16 }}>Self-adapting anomaly threshold converges on live traffic</p>
          <MLCalibrationChart data={calibrationData} />
        </motion.div>
      </div>

      {/* ROW 4 — Cumulative Performance + Latency (50/50) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        <motion.div {...stagger(3)} className="glass-card" style={{ padding: 24 }}>
          <h3 style={{ fontFamily: "'Sora', sans-serif", fontWeight: 600, fontSize: 14, marginBottom: 4 }}>Cumulative Security Performance</h3>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 16 }}>True vs false detections over session lifetime</p>
          <CumulativePerformanceChart data={cumulativeData} />
        </motion.div>
        <motion.div {...stagger(3)} className="glass-card" style={{ padding: 24 }}>
          <h3 style={{ fontFamily: "'Sora', sans-serif", fontWeight: 600, fontSize: 14, marginBottom: 4 }}>Cryptographic Operation Latency</h3>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 16 }}>Per-operation benchmark — NIST Level 5 (AES-256 equivalent)</p>
          <LatencyDistributionChart />
        </motion.div>
      </div>

      {/* ROW 5 — Meter Health Heatmap (full width) */}
      <motion.div {...stagger(4)} className="glass-card" style={{ padding: 24 }}>
        <h3 style={{ fontFamily: "'Sora', sans-serif", fontWeight: 600, fontSize: 14, marginBottom: 4 }}>Meter Security Health Grid</h3>
        <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 16 }}>
          Real-time health score for all {isRunning ? numMeters : '--'} active meters
        </p>
        <MeterHealthHeatmap meterHealth={meterHealth} meterCount={isRunning ? numMeters : 0} />
      </motion.div>
    </div>
  );
}
