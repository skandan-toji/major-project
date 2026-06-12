import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const CT = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'rgba(14,12,26,0.95)', border: '1px solid rgba(124,58,237,0.3)', borderRadius: 10, padding: '10px 14px', backdropFilter: 'blur(10px)', fontSize: 12, fontFamily: 'Inter, sans-serif' }}>
      <p style={{ color: '#5a5a78', marginBottom: 4 }}>{label}</p>
      {payload.map((p, i) => <p key={i} style={{ color: p.color, margin: 0 }}>{p.name}: {p.value}</p>)}
    </div>
  );
};

const grid = { stroke: 'rgba(139,92,246,0.1)' };
const axis = { tick: { fill: '#94a3b8', fontSize: 10 }, axisLine: { stroke: 'rgba(255,255,255,0.08)' } };

export default function DualLayerComparisonChart({ data = [], liveStats }) {
  // Packet-event accumulation — used for the bar chart timeline
  const evtTotals = data.reduce((acc, d) => ({
    crypto: acc.crypto + (d.crypto_only    || 0),
    ml:     acc.ml     + (d.ml_only        || 0),
    both:   acc.both   + (d.both_detected  || 0),
    missed: acc.missed + (d.missed         || 0),
  }), { crypto: 0, ml: 0, both: 0, missed: 0 });

  // Server-side totals are authoritative (computed per-packet on backend, flood-deduped).
  // Fall back to packet-event accumulation only when server hasn't reported yet.
  const serverCrypto = liveStats?.crypto_detections  || 0;
  const serverML     = liveStats?.ml_only_detections || 0;
  const serverBoth   = liveStats?.both_detections    || 0;

  const totalCrypto = serverCrypto > 0 ? serverCrypto : evtTotals.crypto;
  const totalML     = serverML     > 0 ? serverML     : evtTotals.ml;
  const totalBoth   = serverBoth   > 0 ? serverBoth   : evtTotals.both;
  const totalMissed = evtTotals.missed; // packet events for missed (not tracked server-side)

  const totalDetected = totalCrypto + totalML + totalBoth;
  const totalAll      = totalDetected + totalMissed;
  const accuracy      = totalAll > 0 ? ((totalDetected / totalAll) * 100).toFixed(1) : '0.0';

  return (
    <div>
      {/* Summary strip — uses server-side authoritative totals */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 32, marginBottom: 16 }}>
        {[
          { label: 'Crypto Layer',      value: totalCrypto, color: '#8b5cf6' },
          { label: 'ML Layer',          value: totalML,     color: '#06b6d4' },
          { label: 'Both Layers',       value: totalBoth,   color: '#10b981' },
          { label: 'Missed',            value: totalMissed, color: '#ef4444' },
          { label: 'Combined Accuracy', value: `${accuracy}%`, color: '#a78bfa' },
        ].map(s => (
          <div key={s.label} style={{ textAlign: 'center' }}>
            <div className="mono" style={{ fontSize: 18, fontWeight: 600, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 9, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Bar chart timeline — uses packet-event data array for per-interval breakdown */}
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} barCategoryGap="20%">
          <CartesianGrid {...grid} />
          <XAxis dataKey="time" {...axis} label={{ value: 'Session Time', position: 'insideBottom', offset: -2, fill: '#94a3b8', fontSize: 10 }} />
          <YAxis {...axis} label={{ value: 'Detections', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 10 }} />
          <Tooltip content={<CT />} />
          <Legend wrapperStyle={{ fontSize: 10, color: '#94a3b8' }} />
          <Bar dataKey="crypto_only"   fill="#8b5cf6" name="Crypto Layer" radius={[2,2,0,0]} minPointSize={2} />
          <Bar dataKey="ml_only"       fill="#06b6d4" name="ML Layer"     radius={[2,2,0,0]} minPointSize={2} />
          <Bar dataKey="both_detected" fill="#10b981" name="Both Layers"  radius={[2,2,0,0]} minPointSize={2} />
          <Bar dataKey="missed"        fill="#ef4444" name="Missed"       radius={[2,2,0,0]} minPointSize={2} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
