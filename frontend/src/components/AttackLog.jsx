import { motion, AnimatePresence } from 'framer-motion';
import { formatTime } from '../utils/formatters';

export default function AttackLog({ attacks }) {
  return (
    <div style={{ maxHeight: 500, overflowY: 'auto' }}>
      <table className="feed-table">
        <thead>
          <tr><th>Time</th><th>Meter</th><th>Type</th><th>Method</th><th>Action</th></tr>
        </thead>
        <tbody>
          <AnimatePresence initial={false}>
            {attacks.slice(0, 100).map((atk, i) => {
              const typeMap = { replay: 'badge-purple', mitm: 'badge-blue', flood: 'badge-red' };
              const rowBorder = { replay: 'var(--purple-light)', mitm: 'var(--blue-accent)', flood: 'var(--red-danger)' };
              return (
                <motion.tr
                  key={`atk-${atk.timestamp}-${i}`}
                  style={{ borderLeft: `3px solid ${rowBorder[atk.attack_type] || 'var(--text-muted)'}` }}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{formatTime(atk.timestamp)}</td>
                  <td style={{ fontWeight: 600 }}>{atk.meter_id}</td>
                  <td><span className={`badge ${typeMap[atk.attack_type] || 'badge-purple'}`}>{(atk.attack_type || '').toUpperCase()}</span></td>
                  <td><span className="badge badge-cyan">{(atk.detection_method || '').toUpperCase()}</span></td>
                  <td><span className="badge badge-green">BLOCKED</span></td>
                </motion.tr>
              );
            })}
          </AnimatePresence>
        </tbody>
      </table>
    </div>
  );
}
