export default function TrustStrip() {
  const badges = ['NIST FIPS 197', 'CRYSTALS-Dilithium', 'CRYSTALS-Kyber', 'RFC 2104 HMAC', 'NIST PQC Round 3'];
  const doubled = [...badges, ...badges];
  return (
    <section style={{ height: 72, background: 'var(--bg-surface)', borderTop: '1px solid var(--border-subtle)', borderBottom: '1px solid var(--border-subtle)', marginTop: 60, overflow: 'hidden', display: 'flex', alignItems: 'center' }}>
      <div style={{ display: 'flex', animation: 'marquee 20s linear infinite', whiteSpace: 'nowrap' }}>
        {doubled.map((b, i) => (
          <span key={i} style={{ padding: '0 40px', fontSize: 12, fontFamily: "'Inter', sans-serif", fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.05em', textTransform: 'uppercase', borderRight: '1px solid var(--border-subtle)', lineHeight: '72px' }}>{b}</span>
        ))}
      </div>
    </section>
  );
}
