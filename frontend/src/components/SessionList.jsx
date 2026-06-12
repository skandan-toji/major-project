export default function SessionList({ meters = [], isRunning = false }) {
  if (!isRunning || meters.length === 0) {
    return <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 40 }}>No active sessions</div>;
  }
  return (
    <div style={{ maxHeight: 360, overflowY: 'auto' }}>
      {meters.slice(0, 30).map((m, i) => (
        <div key={m.meter_id || i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
          <span className="live-dot online" style={{ width: 6, height: 6 }} />
          <span style={{ fontWeight: 600, fontSize: 13, flex: 1 }}>{m.meter_id}</span>
          <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>{m.packets_sent || 0} pkts</span>
        </div>
      ))}
    </div>
  );
}
