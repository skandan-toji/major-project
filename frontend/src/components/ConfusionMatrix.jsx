import GlassCard from './GlassCard';

export default function ConfusionMatrix({ tp = 0, tn = 0, fp = 0, fn = 0 }) {
  const total = tp + tn + fp + fn || 1;
  return (
    <GlassCard>
      <h3 className="gradient-text" style={{ marginBottom: 16, textAlign: 'center' }}>Confusion Matrix</h3>
      <div style={{ display: 'grid', gridTemplateColumns: '100px 1fr 1fr', gap: 4, maxWidth: 420, margin: '0 auto' }}>
        <div />
        <div className="confusion-label">Pred. Normal</div>
        <div className="confusion-label">Pred. Attack</div>

        <div className="confusion-label" style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}>Actual Normal</div>
        <div className="confusion-cell" style={{ background: 'rgba(16,185,129,0.12)', color: 'var(--green-success)', borderRadius: '8px 0 0 0' }}>
          <div style={{ fontSize: 28, fontWeight: 800 }}>{tn.toLocaleString()}</div>
          <div style={{ fontSize: 11, opacity: 0.7 }}>TN ({(tn/total*100).toFixed(1)}%)</div>
        </div>
        <div className="confusion-cell" style={{ background: 'rgba(239,68,68,0.12)', color: 'var(--red-danger)', borderRadius: '0 8px 0 0' }}>
          <div style={{ fontSize: 28, fontWeight: 800 }}>{fp.toLocaleString()}</div>
          <div style={{ fontSize: 11, opacity: 0.7 }}>FP ({(fp/total*100).toFixed(1)}%)</div>
        </div>

        <div className="confusion-label" style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}>Actual Attack</div>
        <div className="confusion-cell" style={{ background: 'rgba(245,158,11,0.12)', color: 'var(--yellow-warning)', borderRadius: '0 0 0 8px' }}>
          <div style={{ fontSize: 28, fontWeight: 800 }}>{fn.toLocaleString()}</div>
          <div style={{ fontSize: 11, opacity: 0.7 }}>FN ({(fn/total*100).toFixed(1)}%)</div>
        </div>
        <div className="confusion-cell" style={{ background: 'rgba(16,185,129,0.12)', color: 'var(--green-success)', borderRadius: '0 0 8px 0' }}>
          <div style={{ fontSize: 28, fontWeight: 800 }}>{tp.toLocaleString()}</div>
          <div style={{ fontSize: 11, opacity: 0.7 }}>TP ({(tp/total*100).toFixed(1)}%)</div>
        </div>
      </div>
    </GlassCard>
  );
}
