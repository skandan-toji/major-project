import { ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

const CT = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'rgba(14,12,26,0.95)', border: '1px solid rgba(124,58,237,0.3)', borderRadius: 10, padding: '10px 14px', backdropFilter: 'blur(10px)', fontSize: 12, fontFamily: 'Inter, sans-serif' }}>
      <p style={{ color: '#5a5a78', marginBottom: 4 }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color, margin: 0 }}>
          {p.name}: {typeof p.value === 'number' ? (p.value * 100).toFixed(2) + '%' : p.value}
        </p>
      ))}
    </div>
  );
};

const grid = { stroke: 'rgba(139,92,246,0.1)' };
const axis = { tick: { fill: '#94a3b8', fontSize: 10 }, axisLine: { stroke: 'rgba(255,255,255,0.08)' } };

const fmtPct = (v) => `${(v * 100).toFixed(0)}%`;

export default function ErrorRateChart({ data = [] }) {
  return (
    <div>
      <ResponsiveContainer width="100%" height={220}>
        <ComposedChart data={data}>
          <CartesianGrid {...grid} />
          <XAxis dataKey="time" {...axis} />
          <YAxis domain={[0, 0.25]} tickFormatter={fmtPct} {...axis} />
          <Tooltip content={<CT />} />
          <ReferenceLine y={0.25} stroke="rgba(255,255,255,0.2)" strokeDasharray="6 4" label={{ value: 'BB84 Eavesdropping Threshold', fill: '#5a5a78', fontSize: 9, position: 'insideTopRight' }} />
          <Area type="monotone" dataKey="error_rate" stroke="#ef4444" strokeWidth={2} fill="rgba(239,68,68,0.05)" name="System Error Rate" />
          <Line type="monotone" dataKey="attack_intensity" stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="5 3" dot={false} name="Attack Intensity" />
        </ComposedChart>
      </ResponsiveContainer>
      <p style={{ fontSize: 10, color: '#94a3b8', textAlign: 'center', marginTop: 6, fontStyle: 'italic' }}>
        System maintains near-zero error rate regardless of attack intensity
      </p>
    </div>
  );
}
