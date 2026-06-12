import { useMemo, useState, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

/**
 * NetworkMap — Interactive Smart Grid Network Visualization
 * 
 * Meter colors are derived from REAL packet data:
 * - Green (healthy): Most recent packet was accepted, no attacks
 * - Red (attack): Was genuinely attacked (was_attack=true) and rejected
 * - Yellow (suspicious): ML flagged but not confirmed attack
 * - Gray (inactive): No packets processed yet
 * 
 * Click any meter node to see its recent packet history.
 * 
 * Packet flow speed adapts to throughput:
 * - Normal: slow dots (2s transit)
 * - High rate: faster dots (0.5s transit)
 * - Flood attack on meter: many rapid red dots
 */
export default function NetworkMap({ meterCount = 0, packets = [], meterStatuses = {} }) {
  const [selectedMeter, setSelectedMeter] = useState(null);
  const cx = 350, cy = 280;

  // Compute per-meter recent activity for flow speed
  const meterActivity = useMemo(() => {
    const activity = {};
    const recentPkts = (packets || []).slice(0, 50);
    recentPkts.forEach(p => {
      if (!p.meter_id) return;
      if (!activity[p.meter_id]) activity[p.meter_id] = { count: 0, attacks: 0, floods: 0 };
      activity[p.meter_id].count += 1;
      if (p.was_attack) activity[p.meter_id].attacks += 1;
      if (p.attack_type === 'flood') activity[p.meter_id].floods += 1;
    });
    return activity;
  }, [packets]);

  const meters = useMemo(() => {
    const show = Math.min(meterCount, 40);
    const extra = meterCount > 40 ? meterCount - 40 : 0;
    const result = [];
    const rings = [
      { max: 10, r: 130 },
      { max: 15, r: 200 },
      { max: 15, r: 270 },
    ];
    let placed = 0;
    for (const ring of rings) {
      const count = Math.min(ring.max, show - placed);
      for (let i = 0; i < count; i++) {
        const angle = (2 * Math.PI * i) / count - Math.PI / 2;
        const id = `SM_${String(placed + 1).padStart(3, '0')}`;
        const status = meterStatuses[id] || 'inactive';
        result.push({ id, x: cx + ring.r * Math.cos(angle), y: cy + ring.r * Math.sin(angle), status });
        placed++;
      }
      if (placed >= show) break;
    }
    return { nodes: result, extra };
  }, [meterCount, meterStatuses]);

  const statusColor = (s) => s === 'attack' ? '#ef4444' : s === 'suspicious' ? '#f59e0b' : s === 'healthy' ? '#10b981' : '#2a2a40';

  // Get flow speed for a meter
  const getFlowDur = (meterId) => {
    const act = meterActivity[meterId];
    if (!act) return '2s';
    if (act.floods > 0) return '0.3s';
    if (act.count > 5) return '0.5s';
    if (act.count > 2) return '1s';
    return '2s';
  };

  // Get history for selected meter from packets
  const selectedHistory = useMemo(() => {
    if (!selectedMeter) return [];
    return (packets || []).filter(p => p.meter_id === selectedMeter).slice(0, 10);
  }, [selectedMeter, packets]);

  const handleNodeClick = useCallback((meterId) => {
    setSelectedMeter(prev => prev === meterId ? null : meterId);
  }, []);

  const selectedNode = meters.nodes.find(m => m.id === selectedMeter);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <svg viewBox="0 0 700 560" preserveAspectRatio="xMidYMid meet" style={{ width: '100%', height: '100%', maxHeight: '100%', display: 'block' }}>
        {/* Connection lines + animated flow dots */}
        {meters.nodes.map((m, i) => {
          const c = statusColor(m.status);
          const flowDur = getFlowDur(m.id);
          const act = meterActivity[m.id];
          const isFlood = act?.floods > 0;
          const flowColor = isFlood ? '#ef4444' : c;

          return (
            <g key={`l-${i}`}>
              <line x1={cx} y1={cy} x2={m.x} y2={m.y} stroke={c} strokeWidth={1} opacity={0.25} />
              {m.status !== 'inactive' && (
                <>
                  {/* Primary flow dot */}
                  <circle r={3} fill={flowColor} opacity={0.9}>
                    <animateMotion dur={flowDur} repeatCount="indefinite"
                      path={`M ${cx},${cy} L ${m.x},${m.y}`} />
                  </circle>
                  {/* Extra flood dots for high activity */}
                  {isFlood && (
                    <>
                      <circle r={2} fill="#ef4444" opacity={0.7}>
                        <animateMotion dur="0.4s" repeatCount="indefinite" begin="0.1s"
                          path={`M ${cx},${cy} L ${m.x},${m.y}`} />
                      </circle>
                      <circle r={2} fill="#ef4444" opacity={0.5}>
                        <animateMotion dur="0.35s" repeatCount="indefinite" begin="0.2s"
                          path={`M ${cx},${cy} L ${m.x},${m.y}`} />
                      </circle>
                    </>
                  )}
                  {/* Fast dot for high throughput */}
                  {act?.count > 3 && !isFlood && (
                    <circle r={2} fill={flowColor} opacity={0.5}>
                      <animateMotion dur="0.8s" repeatCount="indefinite" begin="0.5s"
                        path={`M ${m.x},${m.y} L ${cx},${cy}`} />
                    </circle>
                  )}
                </>
              )}
            </g>
          );
        })}
        {/* Center hexagon */}
        <polygon points={`${cx},${cy-30} ${cx+26},${cy-15} ${cx+26},${cy+15} ${cx},${cy+30} ${cx-26},${cy+15} ${cx-26},${cy-15}`}
          fill="#7c3aed" stroke="rgba(167,139,250,0.5)" strokeWidth={2}>
          <animate attributeName="opacity" values="0.8;1;0.8" dur="2s" repeatCount="indefinite" />
        </polygon>
        <text x={cx} y={cy + 4} textAnchor="middle" fill="white" fontSize={9} fontFamily="Sora, sans-serif" fontWeight={600}>CC</text>
        <text x={cx} y={cy + 48} textAnchor="middle" fill="var(--text-muted)" fontSize={10}>Control Center</text>

        {/* Meter nodes — clickable */}
        {meters.nodes.map((m, i) => {
          const act = meterActivity[m.id];
          const isFlood = act?.floods > 0;
          return (
            <g key={`n-${i}`} onClick={() => handleNodeClick(m.id)} style={{ cursor: 'pointer' }}>
              {/* Hit area */}
              <circle cx={m.x} cy={m.y} r={16} fill="transparent" />
              {/* Selected ring */}
              {selectedMeter === m.id && (
                <circle cx={m.x} cy={m.y} r={14} fill="none" stroke="#a78bfa" strokeWidth={2} opacity={0.8}>
                  <animate attributeName="r" values="14;17;14" dur="1.5s" repeatCount="indefinite" />
                </circle>
              )}
              {/* Attack ripple */}
              {m.status === 'attack' && (
                <circle cx={m.x} cy={m.y} r={8} fill="none" stroke="#ef4444" strokeWidth={1} opacity={0}>
                  <animate attributeName="r" values="8;22;30" dur="1.5s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.6;0.2;0" dur="1.5s" repeatCount="indefinite" />
                </circle>
              )}
              {/* Main node */}
              <circle cx={m.x} cy={m.y} r={8} fill={statusColor(m.status)} opacity={0.85}>
                {m.status === 'attack' && (
                  <animate attributeName="r" values="8;13;8" dur="1.2s" repeatCount="3" />
                )}
              </circle>
              {/* Flood indicator ring */}
              {isFlood && (
                <circle cx={m.x} cy={m.y} r={11} fill="none" stroke="#ef4444" strokeWidth={1.5} opacity={0.6}>
                  <animate attributeName="opacity" values="0.8;0.2;0.8" dur="0.4s" repeatCount="indefinite" />
                </circle>
              )}
              {/* Meter label */}
              <text x={m.x} y={m.y + 20} textAnchor="middle" fill="var(--text-muted)" fontSize={7} fontFamily="Inter, sans-serif">
                {m.id.replace('SM_', '')}
              </text>
            </g>
          );
        })}
        {meters.extra > 0 && (
          <text x={cx} y={cy + 310} textAnchor="middle" fill="var(--text-muted)" fontSize={11}>...and {meters.extra} more meters</text>
        )}
        {meterCount === 0 && (
          <text x={cx} y={cy + 70} textAnchor="middle" fill="var(--text-muted)" fontSize={13}>Waiting for simulation...</text>
        )}
      </svg>

      {/* Meter Detail Panel — shown on click */}
      <AnimatePresence>
        {selectedMeter && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            style={{
              position: 'absolute', top: 8, right: 8, width: 240,
              background: 'rgba(14,12,26,0.95)', border: '1px solid rgba(124,58,237,0.3)',
              borderRadius: 12, padding: 14, backdropFilter: 'blur(12px)',
              boxShadow: '0 8px 32px rgba(0,0,0,0.5)', zIndex: 10
            }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <span style={{ fontFamily: "'Sora', sans-serif", fontWeight: 600, fontSize: 13 }}>{selectedMeter}</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: statusColor(selectedNode?.status || 'inactive')
                }} />
                <span style={{ fontSize: 10, color: statusColor(selectedNode?.status || 'inactive'), textTransform: 'uppercase', fontWeight: 600 }}>
                  {selectedNode?.status || 'inactive'}
                </span>
                <button onClick={() => setSelectedMeter(null)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 14, padding: '0 2px' }}>✕</button>
              </div>
            </div>
            {/* Stats summary for this meter */}
            {selectedHistory.length > 0 && (() => {
              const lastSeq = selectedHistory[0]?.sequence_number ?? '--';
              const totalPkts = selectedHistory.length;
              const okPkts = selectedHistory.filter(p => p.result === 'accepted').length;
              const failPkts = totalPkts - okPkts;
              const atkPkts = selectedHistory.filter(p => p.was_attack).length;
              return (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginBottom: 10 }}>
                  <div style={{ background: 'rgba(124,58,237,0.08)', borderRadius: 6, padding: '6px 8px', textAlign: 'center' }}>
                    <div className="mono" style={{ fontSize: 16, fontWeight: 600, color: 'var(--purple-glow)' }}>{lastSeq}</div>
                    <div style={{ fontSize: 8, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Last Seq#</div>
                  </div>
                  <div style={{ background: 'rgba(16,185,129,0.08)', borderRadius: 6, padding: '6px 8px', textAlign: 'center' }}>
                    <div className="mono" style={{ fontSize: 16, fontWeight: 600, color: 'var(--green)' }}>{okPkts}/{totalPkts}</div>
                    <div style={{ fontSize: 8, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Accepted</div>
                  </div>
                  {failPkts > 0 && (
                    <div style={{ background: 'rgba(239,68,68,0.08)', borderRadius: 6, padding: '4px 8px', textAlign: 'center' }}>
                      <div className="mono" style={{ fontSize: 13, fontWeight: 600, color: '#ef4444' }}>{failPkts}</div>
                      <div style={{ fontSize: 8, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Rejected</div>
                    </div>
                  )}
                  {atkPkts > 0 && (
                    <div style={{ background: 'rgba(245,158,11,0.08)', borderRadius: 6, padding: '4px 8px', textAlign: 'center' }}>
                      <div className="mono" style={{ fontSize: 13, fontWeight: 600, color: '#f59e0b' }}>{atkPkts}</div>
                      <div style={{ fontSize: 8, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Attacks</div>
                    </div>
                  )}
                </div>
              );
            })()}
            <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>Recent Messages</div>
            {selectedHistory.length === 0 ? (
              <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center', padding: 12 }}>No packets yet</div>
            ) : (
              <div style={{ maxHeight: 200, overflow: 'auto' }}>
                {selectedHistory.map((p, i) => {
                  const ok = p.result === 'accepted';
                  return (
                    <div key={i} style={{ padding: '5px 0', borderBottom: '1px solid rgba(255,255,255,0.04)', fontSize: 10 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span className="mono" style={{ color: 'var(--text-muted)' }}>
                          {p.timestamp ? new Date(p.timestamp * 1000).toLocaleTimeString() : '--'}
                        </span>
                        <span style={{ color: ok ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                          {ok ? '✓ OK' : `✗ ${(p.reason || 'FAIL').slice(0, 8).toUpperCase()}`}
                        </span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 2 }}>
                        <span style={{ color: 'var(--text-muted)' }}>seq: {p.sequence_number ?? '-'}</span>
                        {p.was_attack && <span style={{ color: '#ef4444', fontSize: 9, fontWeight: 600 }}>⚠ ATTACK</span>}
                        {p.ml_flagged && !p.was_attack && <span style={{ color: '#f59e0b', fontSize: 9, fontWeight: 600 }}>ML FLAG</span>}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
