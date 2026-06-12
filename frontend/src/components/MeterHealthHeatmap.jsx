import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';

const getHealthColor = (score) => {
  if (score >= 80) return '#10b981';
  if (score >= 60) return '#34d399';
  if (score >= 40) return '#f59e0b';
  if (score >= 20) return '#f97316';
  return '#ef4444';
};

export default function MeterHealthHeatmap({ meterHealth = {}, meterCount = 0 }) {
  const [hoveredMeter, setHoveredMeter] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const meters = useMemo(() => {
    const count = meterCount || Object.keys(meterHealth).length;
    const result = [];
    for (let i = 1; i <= count; i++) {
      const id = `SM_${String(i).padStart(3, '0')}`;
      const m = meterHealth[id] || { packets_sent: 0, accepted: 0, attacks: 0, fp: 0, health_score: 100 };
      result.push({ id, ...m });
    }
    return result;
  }, [meterHealth, meterCount]);

  if (meters.length === 0) {
    return <div style={{ textAlign: 'center', padding: 40, color: '#5a5a78', fontSize: 13 }}>Waiting for meter data...</div>;
  }

  const sqSize = meters.length <= 50 ? 40 : meters.length <= 100 ? 24 : 12;
  const showLabel = meters.length <= 100;
  const gap = meters.length <= 50 ? 4 : 2;

  return (
    <div>
      <div
        style={{
          display: 'flex', flexWrap: 'wrap', gap, justifyContent: 'center',
          position: 'relative',
        }}
      >
        {meters.map((m, i) => (
          <motion.div
            key={m.id}
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: Math.min(i * 0.005, 0.5), duration: 0.3 }}
            onMouseEnter={(e) => {
              setHoveredMeter(m);
              const rect = e.currentTarget.getBoundingClientRect();
              const parent = e.currentTarget.parentElement.getBoundingClientRect();
              setTooltipPos({ x: rect.left - parent.left + sqSize / 2, y: rect.top - parent.top - 8 });
            }}
            onMouseLeave={() => setHoveredMeter(null)}
            style={{
              width: sqSize, height: sqSize, borderRadius: sqSize <= 12 ? 2 : 4,
              background: getHealthColor(m.health_score),
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer', transition: 'background 0.3s, transform 0.2s',
              border: hoveredMeter?.id === m.id ? '2px solid white' : '1px solid transparent',
              opacity: m.packets_sent === 0 ? 0.3 : 0.85,
            }}
          >
            {showLabel && (
              <span style={{ fontSize: sqSize <= 24 ? 6 : 8, color: 'rgba(0,0,0,0.7)', fontWeight: 700, fontFamily: "'JetBrains Mono', monospace" }}>
                {m.id.replace('SM_', '')}
              </span>
            )}
          </motion.div>
        ))}

        {/* Tooltip */}
        {hoveredMeter && (
          <div style={{
            position: 'absolute',
            left: tooltipPos.x, top: tooltipPos.y,
            transform: 'translate(-50%, -100%)',
            background: 'rgba(14,12,26,0.95)', border: '1px solid rgba(124,58,237,0.3)',
            borderRadius: 10, padding: '10px 14px', backdropFilter: 'blur(10px)',
            fontSize: 11, fontFamily: 'Inter, sans-serif', zIndex: 20,
            pointerEvents: 'none', whiteSpace: 'nowrap',
            boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
          }}>
            <div style={{ fontWeight: 600, color: 'white', marginBottom: 4 }}>{hoveredMeter.id}</div>
            <div style={{ color: getHealthColor(hoveredMeter.health_score), fontWeight: 600 }}>
              Health: {hoveredMeter.health_score.toFixed(0)}/100
            </div>
            <div style={{ color: '#94a3b8' }}>
              Packets: {hoveredMeter.accepted}/{hoveredMeter.packets_sent}
            </div>
            {hoveredMeter.attacks > 0 && (
              <div style={{ color: '#10b981' }}>Attacks detected: {hoveredMeter.attacks}</div>
            )}
            {(hoveredMeter.total_attacks - hoveredMeter.attacks) > 0 && (
              <div style={{ color: '#ef4444' }}>Missed attacks: {hoveredMeter.total_attacks - hoveredMeter.attacks}</div>
            )}
            {hoveredMeter.fp > 0 && (
              <div style={{ color: '#f59e0b' }}>False positives: {hoveredMeter.fp}</div>
            )}
          </div>
        )}
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 12, marginTop: 12 }}>
        {[
          ['#ef4444', '0-40'], ['#f97316', '40-60'], ['#f59e0b', '60-80'], ['#10b981', '80-100']
        ].map(([c, l]) => (
          <div key={l} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 9, color: '#94a3b8' }}>
            <span style={{ width: 10, height: 10, borderRadius: 2, background: c }} />{l}
          </div>
        ))}
      </div>
      <div style={{ textAlign: 'center', color: '#94a3b8', fontSize: 11, marginTop: 8 }}>
        Green = all attacks caught, zero FP. Yellow/Red = attacks slipped through layers.
      </div>
    </div>
  );
}
