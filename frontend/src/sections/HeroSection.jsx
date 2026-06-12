import { motion, useScroll, useTransform } from 'framer-motion';
import { useRef, useState, useEffect } from 'react';
import { useSimulation } from '../context/SimulationContext';
import { formatTime } from '../utils/formatters';

const item = { hidden: { opacity: 0, y: 20 }, visible: i => ({ opacity: 1, y: 0, transition: { delay: i * 0.1, duration: 0.6, ease: [0.22,1,0.36,1] } }) };

/* Decorative doodle SVGs — circuit-inspired shapes */
const doodles = [
  { id: 1, x: '8%', y: '15%', size: 80, speed: -120, rotate: 15, el: (
    <svg viewBox="0 0 80 80" fill="none"><circle cx="40" cy="40" r="28" stroke="#7c3aed" strokeWidth="0.8" opacity="0.5" /><circle cx="40" cy="40" r="16" stroke="#60a5fa" strokeWidth="0.5" opacity="0.4" /><circle cx="40" cy="12" r="3" fill="#a78bfa" opacity="0.6" /><circle cx="40" cy="68" r="2.5" fill="#60a5fa" opacity="0.5" /><line x1="40" y1="15" x2="40" y2="24" stroke="#a78bfa" strokeWidth="0.5" opacity="0.5" /></svg>
  )},
  { id: 2, x: '85%', y: '20%', size: 60, speed: -90, rotate: -20, el: (
    <svg viewBox="0 0 60 60" fill="none"><rect x="10" y="10" width="40" height="40" rx="4" stroke="#7c3aed" strokeWidth="0.7" opacity="0.4" transform="rotate(45 30 30)" /><circle cx="30" cy="30" r="4" fill="#a78bfa" opacity="0.5" /><circle cx="30" cy="8" r="2" fill="#60a5fa" opacity="0.4" /><line x1="30" y1="10" x2="30" y2="20" stroke="#60a5fa" strokeWidth="0.5" opacity="0.4" /></svg>
  )},
  { id: 3, x: '5%', y: '55%', size: 50, speed: -60, rotate: 30, el: (
    <svg viewBox="0 0 50 50" fill="none"><polygon points="25,5 45,35 5,35" stroke="#a78bfa" strokeWidth="0.7" fill="none" opacity="0.4" /><circle cx="25" cy="25" r="3" fill="#7c3aed" opacity="0.5" /></svg>
  )},
  { id: 4, x: '90%', y: '60%', size: 70, speed: -100, rotate: -10, el: (
    <svg viewBox="0 0 70 70" fill="none"><path d="M 10,35 Q 35,5 60,35 Q 35,65 10,35" stroke="#60a5fa" strokeWidth="0.6" fill="none" opacity="0.35" /><circle cx="35" cy="35" r="3" fill="#a78bfa" opacity="0.5" /><circle cx="10" cy="35" r="2" fill="#60a5fa" opacity="0.4" /><circle cx="60" cy="35" r="2" fill="#7c3aed" opacity="0.4" /></svg>
  )},
  { id: 5, x: '15%', y: '80%', size: 45, speed: -50, rotate: 45, el: (
    <svg viewBox="0 0 45 45" fill="none"><line x1="5" y1="22" x2="40" y2="22" stroke="#7c3aed" strokeWidth="0.5" opacity="0.35" /><line x1="22" y1="5" x2="22" y2="40" stroke="#60a5fa" strokeWidth="0.5" opacity="0.35" /><circle cx="22" cy="22" r="4" stroke="#a78bfa" strokeWidth="0.6" fill="none" opacity="0.4" /><circle cx="22" cy="22" r="1.5" fill="#a78bfa" opacity="0.5" /></svg>
  )},
  { id: 6, x: '75%', y: '85%', size: 55, speed: -70, rotate: 20, el: (
    <svg viewBox="0 0 55 55" fill="none"><path d="M27.5 5 L48 17.5 L48 37.5 L27.5 50 L7 37.5 L7 17.5 Z" stroke="#7c3aed" strokeWidth="0.6" fill="none" opacity="0.3" /><circle cx="27.5" cy="27.5" r="3.5" fill="#60a5fa" opacity="0.4" /></svg>
  )},
];

function ParallaxDoodle({ x, y, size, speed, rotate, el, scrollYProgress }) {
  const yMove = useTransform(scrollYProgress, [0, 1], [0, speed]);
  const xMove = useTransform(scrollYProgress, [0, 1], [0, speed * 0.3]);
  const rot = useTransform(scrollYProgress, [0, 1], [rotate, rotate + 30]);
  const opac = useTransform(scrollYProgress, [0, 0.5, 1], [0.14, 0.08, 0.02]);
  return (
    <motion.div className="doodle"
      style={{ left: x, top: y, width: size, height: size, y: yMove, x: xMove, rotate: rot, opacity: opac }}>
      {el}
    </motion.div>
  );
}

function ElapsedTimer({ startTime }) {
  const [elapsed, setElapsed] = useState('00:00');
  useEffect(() => {
    if (!startTime) { setElapsed('00:00'); return; }
    const tick = () => {
      const diff = Math.floor((Date.now() - startTime.getTime()) / 1000);
      const m = String(Math.floor(diff / 60)).padStart(2, '0');
      const s = String(diff % 60).padStart(2, '0');
      setElapsed(`${m}:${s}`);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [startTime]);
  return <span className="mono">{elapsed}</span>;
}

export default function HeroSection({ meterCount, setMeterCount, isRunning, onStart, onStop }) {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end start'] });
  const { liveStats, packetFeed, numMeters, startTime } = useSimulation();

  // Use REAL meter count from backend when running, slider value when idle
  const actualMeters = isRunning ? (liveStats?.meters_online || numMeters) : meterCount;
  const pps = isRunning ? (liveStats?.throughput?.toFixed(1) || '0') : '--';
  const threats = isRunning ? (liveStats?.attacks_detected || 0) : '--';
  const sessionNum = isRunning ? (liveStats?.session_cycle || 1) : '--';

  const recentPkts = isRunning ? (packetFeed || []).slice(0, 3) : [];

  return (
    <section ref={ref} style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', paddingTop: 60, position: 'relative', overflow: 'hidden' }}>
      {doodles.map(d => <ParallaxDoodle key={d.id} {...d} scrollYProgress={scrollYProgress} />)}
      <div style={{ position: 'absolute', bottom: '-10%', left: '50%', transform: 'translateX(-50%)', width: '80%', height: '50%', background: 'radial-gradient(ellipse 80% 50% at 50% 110%, rgba(124,58,237,0.12), transparent)', pointerEvents: 'none' }} />

      <motion.div custom={0} variants={item} initial="hidden" animate="visible" className="shimmer-pill">
        NIST Level 5 &nbsp;·&nbsp; Post-Quantum Cryptography
      </motion.div>

      <motion.h1 custom={1} variants={item} initial="hidden" animate="visible" className="heading-hero" style={{ fontSize: 'clamp(40px, 5.5vw, 64px)', textAlign: 'center', maxWidth: 720, margin: '24px auto 0' }}>
        Quantum-Resilient Security<br />
        <span className="text-gradient">Framework</span>
      </motion.h1>

      <motion.p custom={2} variants={item} initial="hidden" animate="visible" style={{ textAlign: 'center', maxWidth: 480, margin: '20px auto 0', color: 'var(--text-secondary)', fontSize: 16, fontFamily: "'Inter', sans-serif" }}>
        Real-time Man-in-the-Middle attack detection for smart grid infrastructure
      </motion.p>

      {/* Meter slider */}
      <motion.div custom={3} variants={item} initial="hidden" animate="visible" style={{ textAlign: 'center', marginTop: 36 }}>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, marginBottom: 8 }}>Smart Meters</div>
        <div className="mono text-gradient" style={{ fontSize: 48, fontWeight: 600, lineHeight: 1 }}>{isRunning ? actualMeters : meterCount}</div>
        <input type="range" min={10} max={500} step={10} value={meterCount} onChange={e => setMeterCount(+e.target.value)} style={{ marginTop: 12 }} disabled={isRunning} />
        <div style={{ display: 'flex', justifyContent: 'space-between', width: 280, margin: '4px auto 0', fontSize: 10, color: 'var(--text-muted)' }}>
          <span>10</span><span>250</span><span>500</span>
        </div>
      </motion.div>

      {/* Buttons + status */}
      <motion.div custom={4} variants={item} initial="hidden" animate="visible" style={{ display: 'flex', gap: 12, marginTop: 24, alignItems: 'center', flexDirection: 'column' }}>
        {!isRunning ? (
          <button className="btn-primary" style={{ padding: '15px 36px' }} onClick={onStart}>Start Simulation</button>
        ) : (
          <button className="btn-primary btn-danger" style={{ padding: '15px 36px' }} onClick={onStop}>Stop Simulation</button>
        )}
        {isRunning ? (
          <div style={{ display: 'flex', gap: 16, alignItems: 'center', fontSize: 13 }}>
            <span style={{ color: 'var(--green)' }}>● {actualMeters} meters active</span>
            <span style={{ color: 'var(--text-muted)' }}>|</span>
            <span style={{ color: 'var(--cyan)' }}>
              Started: {startTime ? startTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '--'}
            </span>
            <span style={{ color: 'var(--text-muted)' }}>|</span>
            <span style={{ color: 'var(--purple-glow)' }}>Elapsed: <ElapsedTimer startTime={startTime} /></span>
          </div>
        ) : (
          <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>System Ready</span>
        )}
      </motion.div>

      {/* Product Preview Card — live data */}
      <motion.div custom={5} variants={item} initial="hidden" animate="visible" style={{ width: 'min(780px, 92vw)', marginTop: 56 }}>
        <div className="glass-card" style={{ background: 'rgba(14,12,26,0.9)', border: '1px solid rgba(124,58,237,0.3)', borderRadius: 16, boxShadow: '0 0 0 1px rgba(124,58,237,0.15), 0 40px 80px rgba(0,0,0,0.7), 0 0 100px rgba(124,58,237,0.06) inset', overflow: 'hidden' }}>
          {/* Top bar */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', gap: 6 }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#ef4444' }} />
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#f59e0b' }} />
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981' }} />
            </div>
            <span style={{ fontSize: 11, color: isRunning ? 'var(--green)' : 'var(--text-muted)' }}>
              {isRunning ? '● Live Monitoring Active' : '○ Awaiting Simulation'}
            </span>
            <span className="badge badge-purple" style={{ fontSize: 9 }}>SECURED</span>
          </div>
          {/* Stats grid — all from backend */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', padding: 20, gap: 16 }}>
            {[
              ['Active Meters', actualMeters],
              ['Packets/sec', pps],
              ['Threats Blocked', threats],
              ['Session Cycle', sessionNum],
            ].map(([l, v], i) => (
              <div key={i} style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>{l}</div>
                <div className="heading-section text-gradient" style={{ fontSize: 24 }}>{v}</div>
              </div>
            ))}
          </div>
          {/* Mini table — real packet feed */}
          <div style={{ padding: '0 20px 20px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '80px 70px 50px 1fr', gap: 0, fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', paddingBottom: 6, borderBottom: '1px solid var(--border-subtle)' }}>
              <span>TIME</span><span>METER</span><span>SEQ</span><span>RESULT</span>
            </div>
            {recentPkts.length > 0 ? recentPkts.map((p, i) => {
              const accepted = p.result === 'accepted';
              const color = accepted ? 'var(--green)' : 'var(--red)';
              return (
                <div key={i} style={{ display: 'grid', gridTemplateColumns: '80px 70px 50px 1fr', fontSize: 11, fontFamily: "'Inter', sans-serif", padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.02)', borderLeft: `2px solid ${color}`, paddingLeft: 8 }}>
                  <span style={{ color: 'var(--text-muted)' }}>{formatTime(p.timestamp)}</span>
                  <span>{p.meter_id || '--'}</span>
                  <span style={{ color: 'var(--text-muted)' }}>{p.sequence_number ?? '--'}</span>
                  <span style={{ color }}>{accepted ? '✓ ACCEPTED' : `✗ ${(p.reason || '').toUpperCase().slice(0, 12)}`}</span>
                </div>
              );
            }) : (
              <div style={{ padding: '12px 0', textAlign: 'center', fontSize: 11, color: 'var(--text-muted)' }}>
                Start simulation to see live packet data
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </section>
  );
}
