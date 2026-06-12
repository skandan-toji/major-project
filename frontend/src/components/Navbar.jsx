import { NavLink } from 'react-router-dom';
import { useSimulation } from '../context/SimulationContext';
import { useState, useEffect } from 'react';

/* Unique circuit-node logo — 3 connected nodes forming a triangular circuit */
function Logo() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      {/* Triangle circuit paths */}
      <path d="M12 3 L21 18 L3 18 Z" stroke="url(#logoGrad)" strokeWidth="1.5" fill="none" opacity="0.6" />
      {/* Inner connecting lines */}
      <line x1="12" y1="3" x2="12" y2="12" stroke="url(#logoGrad)" strokeWidth="1" opacity="0.4" />
      <line x1="7" y1="15" x2="17" y2="15" stroke="url(#logoGrad)" strokeWidth="1" opacity="0.4" />
      {/* Circuit nodes */}
      <circle cx="12" cy="3" r="2.5" fill="#a78bfa" />
      <circle cx="21" cy="18" r="2.5" fill="#7c3aed" />
      <circle cx="3" cy="18" r="2.5" fill="#60a5fa" />
      {/* Center node — the "brain" */}
      <circle cx="12" cy="12" r="2" fill="url(#logoGrad)" />
      <circle cx="12" cy="12" r="3.5" stroke="#a78bfa" strokeWidth="0.5" fill="none" opacity="0.4">
        <animate attributeName="r" values="3.5;5;3.5" dur="3s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.4;0.1;0.4" dur="3s" repeatCount="indefinite" />
      </circle>
      <defs>
        <linearGradient id="logoGrad" x1="0" y1="0" x2="24" y2="24">
          <stop offset="0%" stopColor="#a78bfa" />
          <stop offset="100%" stopColor="#60a5fa" />
        </linearGradient>
      </defs>
    </svg>
  );
}

export default function Navbar() {
  const { isRunning, wsConnected, liveStats } = useSimulation();
  const [time, setTime] = useState(new Date());
  useEffect(() => { const t = setInterval(() => setTime(new Date()), 1000); return () => clearInterval(t); }, []);

  const statusClass = isRunning ? 'running' : wsConnected ? 'connected' : 'offline';
  const statusLabel = isRunning ? 'LIVE' : wsConnected ? 'CONNECTED' : 'OFFLINE';

  return (
    <nav className="navbar">
      <NavLink to="/" className="navbar-brand">
        <Logo />
        SecureNet
      </NavLink>

      <div className="navbar-links">
        <NavLink to="/live" className={({isActive}) => isActive ? 'active' : ''}>Live Operations</NavLink>
        <NavLink to="/analytics" className={({isActive}) => isActive ? 'active' : ''}>Analytics</NavLink>
        <NavLink to="/attacks" className={({isActive}) => isActive ? 'active' : ''}>Attack Intel</NavLink>
        <NavLink to="/performance" className={({isActive}) => isActive ? 'active' : ''}>Performance</NavLink>
        <NavLink to="/system" className={({isActive}) => isActive ? 'active' : ''}>System Info</NavLink>
      </div>

      <div className="navbar-right">
        <span className={`badge-live ${statusClass}`}>
          <span className="dot" />
          {statusLabel}
        </span>
        {isRunning && liveStats && (
          <>
            <span className="navbar-sep" />
            <span className="mono" style={{ color: 'var(--cyan)', fontSize: 11 }}>
              {(liveStats.throughput || 0).toFixed(1)} pkt/s
            </span>
          </>
        )}
        <span className="navbar-sep" />
        <span style={{ color: 'var(--text-muted)', fontFamily: "'Inter', sans-serif", fontSize: 12 }}>
          {time.toLocaleTimeString()}
        </span>
      </div>
    </nav>
  );
}
