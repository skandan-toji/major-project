import { motion, AnimatePresence } from 'framer-motion';
import { formatTime } from '../utils/formatters';

export default function PacketFeed({ packets }) {
  const visible = packets.slice(0, 50);
  return (
    <div style={{ maxHeight: 420, overflowY: 'auto' }}>
      <table className="feed-table">
        <thead>
          <tr><th>Time</th><th>Meter</th><th>Seq</th><th>Result</th></tr>
        </thead>
        <tbody>
          <AnimatePresence initial={false}>
            {visible.map((pkt, i) => {
              const isAccepted = pkt.result === 'accepted';
              const isFlagged = pkt.ml_flagged && isAccepted;
              const rowClass = isFlagged ? 'feed-row-flagged' : isAccepted ? 'feed-row-accepted' : 'feed-row-rejected';
              let resultText, badgeClass;
              if (isFlagged) { resultText = '! ML FLAG'; badgeClass = 'badge badge-yellow'; }
              else if (isAccepted) { resultText = '+ ACCEPTED'; badgeClass = 'badge badge-green'; }
              else {
                const r = (pkt.reason || '').toUpperCase().replace(/_/g, ' ');
                resultText = '- ' + (r.length > 12 ? r.slice(0, 12) : r);
                badgeClass = 'badge badge-red';
              }
              return (
                <motion.tr
                  key={`${pkt.meter_id}-${pkt.timestamp}-${i}`}
                  className={rowClass}
                  initial={{ opacity: 0, x: 30 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{formatTime(pkt.timestamp)}</td>
                  <td style={{ fontWeight: 600 }}>{pkt.meter_id}</td>
                  <td>{pkt.sequence_number || '--'}</td>
                  <td><span className={badgeClass}>{resultText}</span></td>
                </motion.tr>
              );
            })}
          </AnimatePresence>
        </tbody>
      </table>
    </div>
  );
}
