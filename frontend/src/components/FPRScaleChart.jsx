import { AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, ReferenceArea } from 'recharts';

const CT = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'rgba(14,12,26,0.95)', border: '1px solid rgba(124,58,237,0.3)', borderRadius: 10, padding: '10px 14px', backdropFilter: 'blur(10px)', fontSize: 12, fontFamily: 'Inter, sans-serif' }}>
      <p style={{ color: '#5a5a78', marginBottom: 4 }}>{label} meters</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color, margin: 0 }}>
          {p.name}: {typeof p.value === 'number' ? p.value.toFixed(2) + '%' : '--'}
        </p>
      ))}
    </div>
  );
};

const SCALE_DATA = [
  { meters: 10,  fpr: 0.00, old_fpr: 15.0 },
  { meters: 20,  fpr: 0.00, old_fpr: 23.0 },
  { meters: 50,  fpr: 0.00, old_fpr: 45.0 },
  { meters: 100, fpr: 0.01, old_fpr: 68.0 },
  { meters: 200, fpr: 0.00, old_fpr: 82.0 },
  { meters: 500, fpr: 0.29, old_fpr: null  },
];

const grid = { stroke: 'rgba(139,92,246,0.1)' };
const axis = { tick: { fill: '#94a3b8', fontSize: 10 }, axisLine: { stroke: 'rgba(255,255,255,0.08)' } };

export default function FPRScaleChart() {
  return (
    <div>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={SCALE_DATA}>
          <CartesianGrid {...grid} />
          <ReferenceArea y1={0} y2={0.5} fill="rgba(16,185,129,0.06)" label={{ value: 'Target ≤0.5%', fill: '#10b981', fontSize: 8, position: 'insideTopLeft' }} />
          <XAxis dataKey="meters" type="number" domain={[0, 520]} {...axis} label={{ value: 'Meters', fill: '#94a3b8', fontSize: 10, position: 'insideBottomRight', offset: -5 }} />
          <YAxis domain={[0, 100]} {...axis} tickFormatter={v => `${v}%`} />
          <Tooltip content={<CT />} />
          <Area type="monotone" dataKey="old_fpr" stroke="#ef4444" strokeWidth={2} strokeDasharray="5 3" fill="rgba(239,68,68,0.1)" name="Before Fix" connectNulls={false} />
          <Area type="monotone" dataKey="fpr" stroke="#10b981" strokeWidth={3} fill="rgba(16,185,129,0.05)" name="Current Architecture" />
          <ReferenceLine y={0.5} stroke="rgba(16,185,129,0.4)" strokeDasharray="3 3" />
        </AreaChart>
      </ResponsiveContainer>
      <div style={{ display: 'flex', justifyContent: 'center', gap: 20, marginTop: 8 }}>
        <span style={{ fontSize: 9, color: '#ef4444' }}>━━ Before Fix (up to 82% FPR)</span>
        <span style={{ fontSize: 9, color: '#10b981' }}>━━ Current (0.29% at 500 meters under flood)</span>
      </div>
    </div>
  );
}
