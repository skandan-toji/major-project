import { NavLink } from 'react-router-dom';

export default function FooterSection() {
  return (
    <footer style={{ background: 'var(--bg-surface)', borderTop: '1px solid var(--border-subtle)', padding: '60px 80px 40px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 1fr 1fr', gap: 40, maxWidth: 1200, margin: '0 auto' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M12 3 L21 18 L3 18 Z" stroke="#7c3aed" strokeWidth="1.2" fill="none" opacity="0.6"/><circle cx="12" cy="3" r="2" fill="#a78bfa"/><circle cx="21" cy="18" r="2" fill="#7c3aed"/><circle cx="3" cy="18" r="2" fill="#60a5fa"/><circle cx="12" cy="12" r="1.5" fill="#a78bfa"/></svg>
            <span style={{ fontFamily: "'Sora', sans-serif", fontWeight: 600, fontSize: 16 }}>SecureNet</span>
          </div>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', maxWidth: 220, lineHeight: 1.6 }}>Experience the next generation of smart grid security.</p>
        </div>
        <FooterCol title="Platform" items={[
          { label: 'Live Operations', to: '/live' }, { label: 'Analytics', to: '/analytics' },
          { label: 'Attack Intel', to: '/attacks' }, { label: 'Performance', to: '/performance' },
          { label: 'System Info', to: '/system' },
        ]} />
        <FooterCol title="Security Stack" items={[
          { label: 'Dilithium5' }, { label: 'Kyber1024' }, { label: 'AES-256-GCM' },
          { label: 'HMAC-SHA256' }, { label: 'Isolation Forest' },
        ]} />
        <FooterCol title="Project" items={[
          { label: 'NIST Level 5' }, { label: 'Major Project 2026' },
          { label: 'Detection: 98.18%' }, { label: 'FPR: 0.00%' },
        ]} />
      </div>
      <div style={{ marginTop: 48, borderTop: '1px solid var(--border-subtle)', paddingTop: 24, display: 'flex', justifyContent: 'space-between', maxWidth: 1200, margin: '48px auto 0' }}>
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>©2026 SecureNet. All rights reserved.</span>
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Verified Detection Accuracy: 98.18%</span>
      </div>
    </footer>
  );
}

function FooterCol({ title, items }) {
  return (
    <div>
      <h4 style={{ fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: 16 }}>{title}</h4>
      {items.map((it, i) => (
        it.to ? (
          <NavLink key={i} to={it.to} style={{ display: 'block', fontSize: 13, color: 'var(--text-secondary)', marginBottom: 10, transition: 'color 0.2s' }}
            onMouseEnter={e => e.target.style.color = '#a78bfa'} onMouseLeave={e => e.target.style.color = '#a0a0b8'}>{it.label}</NavLink>
        ) : (
          <div key={i} style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 10 }}>{it.label}</div>
        )
      ))}
    </div>
  );
}
