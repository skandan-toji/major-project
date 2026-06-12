import { ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const CT = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'rgba(14,12,26,0.95)', border: '1px solid rgba(124,58,237,0.3)', borderRadius: 10, padding: '10px 14px', backdropFilter: 'blur(10px)', fontSize: 12, fontFamily: 'Inter, sans-serif' }}>
      <p style={{ color: '#5a5a78', marginBottom: 4 }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color, margin: 0 }}>
          {p.name}: {typeof p.value === 'number'
            ? (p.dataKey === 'precision' ? p.value.toFixed(1) + '%' : p.value)
            : p.value}
        </p>
      ))}
    </div>
  );
};

const grid = { stroke: 'rgba(139,92,246,0.1)' };
const axis = { tick: { fill: '#94a3b8', fontSize: 10 }, axisLine: { stroke: 'rgba(255,255,255,0.08)' } };

export default function CumulativePerformanceChart({ data = [] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <ComposedChart data={data}>
        <CartesianGrid {...grid} />
        <XAxis dataKey="time" {...axis} />
        <YAxis yAxisId="left" {...axis} />
        <YAxis yAxisId="right" orientation="right" domain={[0, 100]} {...axis} tickFormatter={v => `${v}%`} />
        <Tooltip content={<CT />} />
        <Area yAxisId="left" type="monotone" dataKey="cumulative_tp" stroke="#10b981" strokeWidth={2} fill="rgba(16,185,129,0.15)" name="True Positives (Caught)" />
        <Area yAxisId="left" type="monotone" dataKey="cumulative_fp" stroke="#ef4444" strokeWidth={1.5} fill="rgba(239,68,68,0.15)" name="False Positives" />
        <Line yAxisId="right" type="monotone" dataKey="precision" stroke="#a78bfa" strokeWidth={1.5} strokeDasharray="5 3" dot={false} name="Running Precision %" />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
