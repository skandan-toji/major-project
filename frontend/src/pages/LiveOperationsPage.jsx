import { motion, AnimatePresence } from 'framer-motion';
import { useSimulation } from '../context/SimulationContext';
import { formatTime } from '../utils/formatters';
import NetworkMap from '../components/NetworkMap';

export default function LiveOperationsPage() {
  const { liveStats, packetFeed, attackLog, sessions, isRunning, numMeters } = useSimulation();
  const recent = (packetFeed || []).slice(0, 30);
  const accepted = liveStats?.accepted || 0;
  const rejected = liveStats?.rejected || 0;
  const attacks = liveStats?.attacks_detected || 0;
  const pps = liveStats?.throughput || 0;

  // ── Meter status colors from REAL backend session data ──
  // sessions[] comes from /api/sessions/active which includes is_attack_session
  // from the AttackSessionManager (15% attack session probability)
  //
  // Logic:
  //   - "attack" (red)     = is_attack_session=true AND has detected attacks
  //   - "suspicious" (yellow) = is_attack_session=true BUT no attacks detected yet
  //   - "healthy" (green)   = normal session (is_attack_session=false)
  //   - "inactive" (gray)   = no session data yet
  const meterStatuses = {};
  (sessions || []).forEach(s => {
    if (s.is_attack_session && s.attacks > 0) {
      meterStatuses[s.meter_id] = 'attack';
    } else if (s.is_attack_session) {
      meterStatuses[s.meter_id] = 'suspicious';
    } else if (s.active) {
      meterStatuses[s.meter_id] = 'healthy';
    }
  });

  return (
    <div style={{ position: 'relative', zIndex: 1 }}>
      <div style={{ padding: '80px 24px 24px' }}>
        <h1 className="heading-section text-gradient" style={{ fontSize: 'clamp(24px,3vw,32px)', marginBottom: 4 }}>Live Operations</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 20 }}>Real-time monitoring dashboard</p>

        {/* Top stats bar */}
        <div className="glass-card" style={{ padding: '12px 20px', marginBottom: 16, display: 'flex', justifyContent: 'space-around', textAlign: 'center' }}>
          {[
            { label: 'Packets', value: liveStats?.total_packets || 0, color: 'var(--text-primary)' },
            { label: 'Accepted', value: accepted, color: 'var(--green)' },
            { label: 'Rejected', value: rejected, color: 'var(--red)' },
            { label: 'Attacks', value: attacks, color: 'var(--yellow)' },
            { label: 'Throughput', value: `${pps.toFixed(1)}/s`, color: 'var(--cyan)' },
          ].map((s, i) => (
            <div key={i}>
              <div className="mono" style={{ fontSize: 18, fontWeight: 600, color: s.color }}>{s.value}</div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{s.label}</div>
            </div>
          ))}
        </div>

        <div className="three-col" style={{ display: 'grid', gridTemplateColumns: '240px 1fr 320px', gap: 16, height: 'calc(100vh - 230px)', minHeight: 500 }}>
          {/* LEFT — Sessions */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, overflow: 'hidden' }}>
            <div className="glass-card" style={{ padding: 16, flex: 1, overflow: 'auto', minHeight: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <span className="heading-card" style={{ fontSize: 13 }}>Sessions</span>
                <span className="badge badge-purple">{(sessions || []).length}</span>
              </div>
              {(!sessions || sessions.length === 0) ? (
                <p style={{ color: 'var(--text-muted)', fontSize: 12, textAlign: 'center', marginTop: 30 }}>No active sessions</p>
              ) : (
                (sessions || []).slice(0, 30).map((s, i) => {
                  const statusBadge = s.is_attack_session
                    ? (s.attacks > 0 ? 'badge-red' : 'badge-yellow')
                    : 'badge-green';
                  const statusLabel = s.is_attack_session
                    ? (s.attacks > 0 ? 'THREAT' : 'WATCH')
                    : 'SAFE';
                  return (
                    <div key={i} style={{ padding: '6px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontFamily: "'Sora', sans-serif", fontWeight: 600, fontSize: 12 }}>{s.meter_id}</span>
                        <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                          <span className="badge badge-purple" style={{ fontSize: 7, padding: '1px 4px' }}>S{s.session_cycle || 1}</span>
                          <span className={`badge ${statusBadge}`} style={{ fontSize: 7, padding: '1px 4px' }}>{statusLabel}</span>
                        </div>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: 'var(--text-muted)' }}>
                        <span className="mono">{s.packets_sent || 0} pkts</span>
                        {s.attacks > 0 && <span style={{ color: 'var(--red)', fontSize: 8 }}>⚠ {s.attacks} atk</span>}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
            <div className="glass-card" style={{ padding: 16, flexShrink: 0 }}>
              <span className="heading-card" style={{ fontSize: 13, display: 'block', marginBottom: 8 }}>System Health</span>
              {['Crypto', 'ML Model', 'Sessions', 'Attack Detect'].map(s => (
                <div key={s} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: 12 }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                    <span style={{ width: 5, height: 5, borderRadius: '50%', background: isRunning ? 'var(--green)' : 'var(--text-muted)' }} />{s}
                  </span>
                  <span style={{ color: isRunning ? 'var(--green)' : 'var(--text-muted)', fontSize: 10 }}>{isRunning ? 'OK' : '—'}</span>
                </div>
              ))}
            </div>
          </div>

          {/* CENTER — Network Map */}
          <div className="glass-card" style={{ padding: 16, overflow: 'hidden', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, flexShrink: 0 }}>
              <span className="heading-card" style={{ fontSize: 13 }}>Smart Grid Network</span>
              <span className="badge badge-green">{liveStats?.total_packets || 0} PKT</span>
            </div>
            <div style={{ flex: 1, minHeight: 0, maxHeight: '100%', position: 'relative' }}>
              <NetworkMap meterCount={isRunning ? (numMeters || 100) : 0} packets={packetFeed} meterStatuses={meterStatuses} />
            </div>
            {/* Legend */}
            <div style={{ flexShrink: 0, marginTop: 6, display: 'flex', gap: 16, justifyContent: 'center', paddingTop: 6, borderTop: '1px solid var(--border-subtle)' }}>
              {[['#10b981','Normal'],['#f59e0b','Attack Session'],['#ef4444','Threat Detected']].map(([c,l]) => (
                <div key={l} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 9, color: 'var(--text-muted)' }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: c }} />{l}
                </div>
              ))}
            </div>
          </div>

          {/* RIGHT — Packet Feed */}
          <div className="glass-card" style={{ padding: 16, overflow: 'hidden', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, flexShrink: 0 }}>
              <span className="heading-card" style={{ fontSize: 13 }}>Packet Feed</span>
              <span className="badge badge-blue">{pps.toFixed(1)} PKT/S</span>
            </div>
            <div style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
              <table className="feed-table">
                <thead><tr><th>TIME</th><th>METER</th><th>SEQ</th><th>RESULT</th></tr></thead>
                <tbody>
                  <AnimatePresence initial={false}>
                    {recent.map((p, i) => {
                      const isAccepted = p.result === 'accepted';
                      return (
                        <motion.tr key={`${p.meter_id}-${p.sequence_number}-${i}`}
                          className={isAccepted ? 'feed-row-accepted' : p.was_attack ? 'feed-row-flagged' : 'feed-row-rejected'}
                          initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.3 }}>
                          <td style={{ color: 'var(--text-muted)', fontSize: 10 }}>{formatTime(p.timestamp)}</td>
                          <td style={{ fontSize: 11 }}>{p.meter_id || '--'}</td>
                          <td className="mono" style={{ fontSize: 10, color: 'var(--text-muted)' }}>{p.sequence_number ?? '--'}</td>
                          <td style={{ color: isAccepted ? 'var(--green)' : 'var(--red)', fontSize: 10, fontWeight: 600 }}>
                            {isAccepted ? '✓' : '✗'} {(p.reason || 'OK').toUpperCase().slice(0, 10)}
                          </td>
                        </motion.tr>
                      );
                    })}
                  </AnimatePresence>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
