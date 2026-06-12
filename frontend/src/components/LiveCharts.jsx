import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, Area, AreaChart } from 'recharts';
import GlassCard from './GlassCard';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <div className="label">{label}</div>
      {payload.map((p, i) => <div key={i} className="value" style={{ color: p.color }}>{p.name}: {typeof p.value === 'number' ? p.value.toFixed(2) : p.value}</div>)}
    </div>
  );
};

export function ThroughputChart({ data }) {
  return (
    <GlassCard><h4 style={{ marginBottom: 12, color: 'var(--text-secondary)' }}>Packets Per Second</h4>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="time" /><YAxis />
          <Tooltip content={<CustomTooltip />} /><Area type="monotone" dataKey="pps" stroke="#06b6d4" fill="rgba(6,182,212,0.1)" strokeWidth={2} /></AreaChart>
      </ResponsiveContainer>
    </GlassCard>
  );
}

export function DetectionChart({ data }) {
  return (
    <GlassCard><h4 style={{ marginBottom: 12, color: 'var(--text-secondary)' }}>Detection Accuracy Over Time</h4>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="time" /><YAxis domain={[0, 100]} />
          <Tooltip content={<CustomTooltip />} /><Line type="monotone" dataKey="accuracy" stroke="#10b981" strokeWidth={2} dot={false} /></LineChart>
      </ResponsiveContainer>
    </GlassCard>
  );
}

const COLORS = ['#a78bfa', '#3b82f6', '#ef4444'];
export function AttackPieChart({ data }) {
  const total = data.reduce((s, d) => s + d.value, 0);
  return (
    <GlassCard><h4 style={{ marginBottom: 12, color: 'var(--text-secondary)' }}>Attack Distribution</h4>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart><Pie data={data} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} ${(percent*100).toFixed(0)}%`}>
          {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
        </Pie><Tooltip content={<CustomTooltip />} /></PieChart>
      </ResponsiveContainer>
      <div style={{ textAlign: 'center', fontSize: 13, color: 'var(--text-muted)' }}>Total: {total}</div>
    </GlassCard>
  );
}

export function ScoreChart({ data }) {
  return (
    <GlassCard><h4 style={{ marginBottom: 12, color: 'var(--text-secondary)' }}>ML Anomaly Scores</h4>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="time" /><YAxis />
          <Tooltip content={<CustomTooltip />} /><Bar dataKey="score" fill="#3b82f6" radius={[4,4,0,0]} /></BarChart>
      </ResponsiveContainer>
    </GlassCard>
  );
}

export function RejectionChart({ data }) {
  return (
    <GlassCard><h4 style={{ marginBottom: 12, color: 'var(--text-secondary)' }}>Rejection Breakdown</h4>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} layout="vertical"><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" /><YAxis dataKey="name" type="category" width={100} />
          <Tooltip content={<CustomTooltip />} /><Bar dataKey="count" fill="#8b5cf6" radius={[0,4,4,0]} /></BarChart>
      </ResponsiveContainer>
    </GlassCard>
  );
}

export function MeterHeatmap({ meters = [] }) {
  if (!meters.length) return <GlassCard><h4 style={{ marginBottom: 12, color: 'var(--text-secondary)' }}>Per-Meter FPR</h4><p style={{ color: 'var(--text-muted)' }}>Waiting for data...</p></GlassCard>;
  return (
    <GlassCard><h4 style={{ marginBottom: 12, color: 'var(--text-secondary)' }}>Per-Meter FPR</h4>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
        {meters.slice(0, 100).map((m, i) => {
          const fpr = m.false_positives / (m.packets_sent || 1);
          const color = fpr === 0 ? '#10b981' : fpr < 0.01 ? '#f59e0b' : '#ef4444';
          return <div key={i} title={`${m.meter_id}: FPR ${(fpr*100).toFixed(2)}%`} style={{ width: 14, height: 14, borderRadius: 3, background: color, opacity: 0.8 }} />;
        })}
      </div>
    </GlassCard>
  );
}
