import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine, ReferenceArea } from 'recharts';

const CT = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  return (
    <div style={{ background: 'rgba(14,12,26,0.95)', border: '1px solid rgba(124,58,237,0.3)', borderRadius: 10, padding: '10px 14px', backdropFilter: 'blur(10px)', fontSize: 12, fontFamily: 'Inter, sans-serif' }}>
      <p style={{ color: 'white', fontWeight: 600, marginBottom: 4 }}>{d?.name}</p>
      <p style={{ color: payload[0]?.color, margin: 0 }}>Average: {d?.avg?.toFixed(2)}ms</p>
    </div>
  );
};

const LATENCY_DATA = [
  { name: 'Dilithium5 Sign', avg: 0.73 },
  { name: 'Dilithium5 Verify', avg: 0.23 },
  { name: 'Kyber1024 Encrypt', avg: 0.17 },
  { name: 'Kyber1024 Decrypt', avg: 0.07 },
  { name: 'AES-256-GCM Enc', avg: 1.15 },
  { name: 'AES-256-GCM Dec', avg: 0.08 },
  { name: 'HMAC Compute', avg: 0.04 },
  { name: 'HMAC Verify', avg: 0.03 },
];

const getColor = (v) => v < 0.5 ? '#10b981' : v <= 1.5 ? '#8b5cf6' : '#06b6d4';

const grid = { stroke: 'rgba(139,92,246,0.1)' };
const axis = { tick: { fill: '#94a3b8', fontSize: 9 }, axisLine: { stroke: 'rgba(255,255,255,0.08)' } };

export default function LatencyDistributionChart() {
  return (
    <div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={LATENCY_DATA} layout="vertical" barCategoryGap="15%">
          <CartesianGrid {...grid} />
          <ReferenceArea x1={0} x2={1} fill="rgba(16,185,129,0.03)" />
          <ReferenceArea x1={1} x2={2} fill="rgba(139,92,246,0.03)" />
          <ReferenceArea x1={2} x2={3} fill="rgba(245,158,11,0.03)" />
          <XAxis type="number" domain={[0, 3]} {...axis} tickFormatter={v => `${v}ms`} />
          <YAxis dataKey="name" type="category" {...axis} width={120} />
          <Tooltip content={<CT />} cursor={{ fill: 'rgba(139,92,246,0.05)' }} />
          <ReferenceLine x={10} stroke="rgba(239,68,68,0.3)" strokeDasharray="5 3" label={{ value: 'NIST L5 10ms', fill: '#ef4444', fontSize: 8, position: 'insideTopRight' }} />
          <Bar dataKey="avg" radius={[0, 4, 4, 0]} label={{ position: 'right', fill: '#94a3b8', fontSize: 9, formatter: v => `${v}ms` }}>
            {LATENCY_DATA.map((d, i) => <Cell key={i} fill={getColor(d.avg)} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div style={{ display: 'flex', justifyContent: 'center', gap: 16, marginTop: 8 }}>
        {[['#10b981', '< 0.5ms Excellent'], ['#8b5cf6', '0.5-1.5ms Good'], ['#06b6d4', '> 1.5ms Acceptable']].map(([c, l]) => (
          <div key={l} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 9, color: '#94a3b8' }}>
            <span style={{ width: 8, height: 8, borderRadius: 2, background: c }} />{l}
          </div>
        ))}
      </div>
      <p style={{ fontSize: 10, color: '#10b981', textAlign: 'center', marginTop: 6 }}>
        All operations sub-2ms · NIST Level 5 compliant at 500 concurrent meters
      </p>
    </div>
  );
}
