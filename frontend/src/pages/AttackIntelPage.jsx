import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSimulation } from '../context/SimulationContext';
import { formatTime } from '../utils/formatters';

const typeColor = { replay: 'badge-purple', mitm: 'badge-blue', flood: 'badge-red', unknown: 'badge-yellow' };
const borderColor = { replay: 'var(--purple-core)', mitm: 'var(--blue-core)', flood: 'var(--red)', unknown: 'var(--yellow)' };

export default function AttackIntelPage() {
  const { attackLog, attackSummary, liveStats } = useSimulation();
  const [selectedMeter, setSelectedMeter] = useState('all');

  const atks = attackLog || [];

  // Get unique meters from attack log
  const meterIds = useMemo(() => {
    const ids = new Set(atks.map(a => a.meter_id).filter(Boolean));
    return Array.from(ids).sort();
  }, [atks]);

  // Filter attacks by selected meter
  const filteredAtks = useMemo(() => {
    if (selectedMeter === 'all') return atks;
    return atks.filter(a => a.meter_id === selectedMeter);
  }, [atks, selectedMeter]);

  // Compute summary for filtered view
  const filteredSummary = useMemo(() => {
    const counts = { replay: 0, mitm: 0, flood: 0, unknown: 0, total: 0 };
    filteredAtks.forEach(a => {
      const t = (a.attack_type || 'unknown').toLowerCase();
      if (t in counts) counts[t] += 1;
      else counts.unknown += 1;
    });
    counts.total = filteredAtks.length;
    return counts;
  }, [filteredAtks]);

  const total = filteredSummary.total;
  const metersHit = new Set(atks.map(a => a.meter_id)).size;
  const topType = Object.entries(filteredSummary).filter(([k]) => k !== 'total' && k !== 'unknown').sort((a, b) => b[1] - a[1])[0];

  return (
    <div style={{ position: 'relative', zIndex: 1, padding: '100px 40px 40px', maxWidth: 1280, margin: '0 auto' }}>
      <h1 className="heading-section text-gradient" style={{ textAlign: 'center', fontSize: 'clamp(28px,4vw,36px)', marginBottom: 4 }}>Attack Intelligence</h1>
      <p style={{ textAlign: 'center', color: 'var(--text-secondary)', fontSize: 14, marginBottom: 24 }}>Real-time threat monitoring and analysis</p>

      {/* Meter filter */}
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 24 }}>
        <div className="glass-card" style={{ display: 'inline-flex', alignItems: 'center', gap: 12, padding: '10px 20px' }}>
          <span style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Filter by Meter:</span>
          <select
            value={selectedMeter}
            onChange={e => setSelectedMeter(e.target.value)}
            style={{
              background: 'var(--bg-elevated)', color: 'var(--text-primary)',
              border: '1px solid var(--border-subtle)', borderRadius: 8,
              padding: '6px 12px', fontSize: 12, fontFamily: "'Sora', sans-serif",
              cursor: 'pointer', outline: 'none',
            }}>
            <option value="all">All Meters ({atks.length} attacks)</option>
            {meterIds.map(id => {
              const count = atks.filter(a => a.meter_id === id).length;
              return <option key={id} value={id}>{id} ({count} attacks)</option>;
            })}
          </select>
          {selectedMeter !== 'all' && (
            <button onClick={() => setSelectedMeter('all')}
              style={{ background: 'none', border: '1px solid var(--border-subtle)', borderRadius: 6, color: 'var(--text-muted)', padding: '4px 10px', fontSize: 11, cursor: 'pointer' }}>
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Summary cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 28 }}>
        {[
          { label: 'Total Detected', value: total, color: 'var(--red)' },
          { label: 'Most Common', value: topType && topType[1] > 0 ? topType[0].toUpperCase() : '--', color: 'var(--purple-bright)' },
          { label: 'Meters Targeted', value: metersHit || '--', color: 'var(--yellow)', subLabel: (liveStats?.detection_accuracy || 0) >= 95 ? 'All attacks detected' : 'Some attacks missed', subColor: (liveStats?.detection_accuracy || 0) >= 95 ? '#10b981' : 'var(--yellow)' },
          { label: 'Detection Rate', value: `${(liveStats?.detection_accuracy || 0).toFixed(1)}%`, color: 'var(--green)' },
        ].map((c, i) => (
          <div key={i} className="glass-card" style={{ padding: 24, textAlign: 'center', borderBottom: `3px solid ${c.color}` }}>
            <div className="mono" style={{ fontSize: 32, fontWeight: 600, background: `linear-gradient(135deg, ${c.color}, var(--purple-glow))`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
              {c.value}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 6 }}>{c.label}</div>
            {c.subLabel && (
              <div style={{ fontSize: 10, color: c.subColor, marginTop: 4, fontWeight: 500 }}>{c.subLabel}</div>
            )}
          </div>
        ))}
      </div>

      {/* Main content */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: 20 }}>
        {/* Attack Log — shows all filtered attacks */}
        <div className="glass-card" style={{ padding: 24, maxHeight: 520, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexShrink: 0 }}>
            <h3 style={{ fontFamily: "'Sora', sans-serif", fontWeight: 600, fontSize: 14, margin: 0 }}>
              Attack Event Log {selectedMeter !== 'all' && <span style={{ color: 'var(--cyan)', fontSize: 12 }}>— {selectedMeter}</span>}
            </h3>
            <span className="badge badge-red">{filteredAtks.length}</span>
          </div>
          <div style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
            <table className="feed-table">
              <thead><tr><th>TIME</th><th>METER</th><th>TYPE</th><th>METHOD</th><th>ACTION</th></tr></thead>
              <tbody>
                <AnimatePresence initial={false}>
                  {filteredAtks.slice(0, 200).map((a, i) => (
                    <motion.tr key={`${a.meter_id}-${a.timestamp}-${i}`}
                      initial={{ opacity: 0, y: -10, backgroundColor: 'rgba(239,68,68,0.12)' }}
                      animate={{ opacity: 1, y: 0, backgroundColor: 'rgba(239,68,68,0)' }}
                      transition={{ duration: 0.5 }}
                      style={{ borderLeft: `2px solid ${borderColor[a.attack_type] || 'var(--red)'}`, cursor: 'pointer' }}
                      onClick={() => setSelectedMeter(a.meter_id)}>
                      <td style={{ fontSize: 11, color: 'var(--text-muted)' }}>{formatTime(a.timestamp)}</td>
                      <td style={{ fontSize: 11 }}>{a.meter_id || '--'}</td>
                      <td><span className={`badge ${typeColor[a.attack_type] || 'badge-red'}`}>{(a.attack_type || '').toUpperCase()}</span></td>
                      <td style={{ fontSize: 10, color: 'var(--text-muted)' }}>{a.detection_method || '--'}</td>
                      <td style={{ fontSize: 11, color: 'var(--green)', fontWeight: 600 }}>DETECTED</td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
            {filteredAtks.length === 0 && <p style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: 40, fontSize: 13 }}>No attacks detected{selectedMeter !== 'all' ? ` for ${selectedMeter}` : ' yet'}</p>}
          </div>
        </div>

        {/* Right panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Attack Timeline */}
          <div className="glass-card" style={{ padding: 24, flex: 1, overflow: 'auto', maxHeight: 280 }}>
            <h3 style={{ fontFamily: "'Sora', sans-serif", fontWeight: 600, fontSize: 14, marginBottom: 16 }}>Attack Timeline</h3>
            {filteredAtks.slice(0, 12).map((a, i) => (
              <div key={i} style={{ display: 'flex', gap: 12, marginBottom: 14, cursor: 'pointer' }}
                onClick={() => setSelectedMeter(a.meter_id)}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: borderColor[a.attack_type] || 'var(--red)' }} />
                  {i < 11 && <div style={{ width: 1, flex: 1, background: 'var(--border-subtle)', marginTop: 4 }} />}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                    <strong style={{ color: 'white' }}>{a.meter_id}</strong> — {(a.attack_type || '').charAt(0).toUpperCase() + (a.attack_type || '').slice(1)} Attack
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Detected via {a.detection_method || 'crypto layer'} · {formatTime(a.timestamp)}</div>
                </div>
              </div>
            ))}
            {filteredAtks.length === 0 && <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Waiting for attacks...</p>}
          </div>

          {/* Attack type distribution */}
          <div className="glass-card" style={{ padding: 24 }}>
            <h3 style={{ fontFamily: "'Sora', sans-serif", fontWeight: 600, fontSize: 14, marginBottom: 16 }}>
              Type Distribution {selectedMeter !== 'all' && <span style={{ color: 'var(--cyan)', fontSize: 11 }}>({selectedMeter})</span>}
            </h3>
            {['replay', 'mitm', 'flood'].map(type => {
              const count = filteredSummary[type] || 0;
              const pct = total > 0 ? ((count / total) * 100).toFixed(1) : '0.0';
              const barWidth = total > 0 ? `${(count / total) * 100}%` : '0%';
              return (
                <div key={type} style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                    <span style={{ color: 'var(--text-secondary)', textTransform: 'uppercase' }}>{type}</span>
                    <span className="mono" style={{ color: 'var(--text-primary)' }}>{count} ({pct}%)</span>
                  </div>
                  <div style={{ height: 6, background: 'var(--bg-elevated)', borderRadius: 3 }}>
                    <div style={{ height: '100%', width: barWidth, background: borderColor[type], borderRadius: 3, transition: 'width 0.5s' }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
