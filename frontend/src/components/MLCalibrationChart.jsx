import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, ReferenceArea } from 'recharts';

const CT = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'rgba(14,12,26,0.95)', border: '1px solid rgba(124,58,237,0.3)', borderRadius: 10, padding: '10px 14px', backdropFilter: 'blur(10px)', fontSize: 12, fontFamily: 'Inter, sans-serif' }}>
      <p style={{ color: '#5a5a78', marginBottom: 4 }}>Sample #{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color, margin: 0 }}>
          {p.name}: {typeof p.value === 'number' ? p.value.toFixed(4) : '--'}
        </p>
      ))}
    </div>
  );
};

const grid = { stroke: 'rgba(139,92,246,0.1)' };
const axis = { tick: { fill: '#94a3b8', fontSize: 10 }, axisLine: { stroke: 'rgba(255,255,255,0.08)' } };

export default function MLCalibrationChart({ data = [] }) {
  const lastPoint = data.length > 0 ? data[data.length - 1] : null;
  const calibrated = lastPoint?.calibrated === true;
  const scoreMean = lastPoint?.score_mean;
  const scoreStd = lastPoint?.score_std;

  // Build band data if we have mean/std
  const bandData = (scoreMean != null && scoreStd != null && scoreStd > 0)
    ? data.map(d => ({
        ...d,
        band_upper: (d.score_mean || scoreMean) + 4 * (d.score_std || scoreStd),
        band_lower: (d.score_mean || scoreMean) - 4 * (d.score_std || scoreStd),
      }))
    : data;

  return (
    <div>
      {/* Calibration status badge */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {calibrated ? (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 10px', borderRadius: 100, background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.3)', color: '#10b981', fontSize: 10, fontWeight: 600, letterSpacing: '0.04em' }}>
              <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#10b981' }} /> CALIBRATED
            </span>
          ) : (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 10px', borderRadius: 100, background: 'rgba(245,158,11,0.12)', border: '1px solid rgba(245,158,11,0.3)', color: '#f59e0b', fontSize: 10, fontWeight: 600, letterSpacing: '0.04em', animation: 'live-pulse 2s ease-in-out infinite' }}>
              ⟳ CALIBRATING...
            </span>
          )}
        </div>
        {lastPoint && (
          <span className="mono" style={{ fontSize: 10, color: '#94a3b8' }}>
            {lastPoint.samples_collected || 0} / 100 samples
          </span>
        )}
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={bandData.length > 0 ? bandData : [{ samples_collected: 0 }]}>
          <CartesianGrid {...grid} />
          <XAxis dataKey="samples_collected" type="number" domain={[0, 'auto']} {...axis} />
          <YAxis {...axis} />
          <Tooltip content={<CT />} />
          <ReferenceLine x={100} stroke="rgba(16,185,129,0.5)" strokeDasharray="5 3" label={{ value: 'Calibration Complete', fill: '#10b981', fontSize: 8, position: 'insideTopRight' }} />
          {scoreMean != null && <ReferenceArea y1={scoreMean - 4 * (scoreStd || 0.01)} y2={scoreMean + 4 * (scoreStd || 0.01)} fill="rgba(139,92,246,0.06)" />}
          <Line type="monotone" dataKey="current_threshold" stroke="#8b5cf6" strokeWidth={2} dot={false} name="Effective Threshold" connectNulls />
          <Line type="monotone" dataKey="score_mean" stroke="#06b6d4" strokeWidth={1.5} strokeDasharray="5 3" dot={false} name="Score Mean" connectNulls />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
