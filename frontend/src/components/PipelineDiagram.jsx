import { motion } from 'framer-motion';

const layers = [
  { icon: '🔐', name: 'Dilithium5', desc: 'Digital Signatures', metric: 'Sign: 0.73ms | Verify: 0.23ms' },
  { icon: '🔑', name: 'Kyber1024', desc: 'Key Encapsulation', metric: 'Enc: 0.17ms | Dec: 0.07ms' },
  { icon: '🛡️', name: 'AES-256-GCM', desc: 'Authenticated Encryption', metric: 'Enc: 1.15ms | Dec: 0.08ms' },
  { icon: '✅', name: 'HMAC-SHA256', desc: 'Message Integrity', metric: 'Compute: ~0.03ms' },
  { icon: '🔢', name: 'Seq + Timestamp', desc: 'Replay Prevention', metric: 'Window: 60s' },
  { icon: '📋', name: 'Session Mgmt', desc: 'Session Lifecycle', metric: 'Lifetime: 900s' },
  { icon: '🤖', name: 'Isolation Forest', desc: 'ML Anomaly Detection', metric: 'Accuracy: 98.04%' },
];

export default function PipelineDiagram({ large = false }) {
  return (
    <div className="pipeline-row">
      {layers.map((layer, i) => (
        <motion.div key={layer.name} style={{ display: 'flex', alignItems: 'center' }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.08, duration: 0.4 }}
        >
          <div className="pipeline-node glass-card" style={{ padding: large ? '20px 24px' : '12px 16px' }}>
            <div className="node-icon" style={{ fontSize: large ? 24 : 20 }}>{layer.icon}</div>
            <div className="node-name" style={{ fontSize: large ? 15 : 13 }}>{layer.name}</div>
            <div className="node-desc">{layer.desc}</div>
            {large && <div className="node-metric">{layer.metric}</div>}
          </div>
          {i < layers.length - 1 && <span className="pipeline-arrow">→</span>}
        </motion.div>
      ))}
    </div>
  );
}
