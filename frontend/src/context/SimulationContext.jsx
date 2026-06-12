import { createContext, useContext, useState, useCallback, useRef, useEffect, useMemo } from 'react';
import { useWebSocket } from '../websocket/useWebSocket';
import api from '../utils/api';

const SimulationContext = createContext(null);

export function SimulationProvider({ children }) {
  const [isRunning, setIsRunning] = useState(false);
  const [numMeters, setNumMeters] = useState(100);
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [attackSummary, setAttackSummary] = useState({ replay: 0, mitm: 0, flood: 0, unknown: 0, total: 0 });
  const [startTime, setStartTime] = useState(null);

  // ── NEW: Analytics chart data ─────────────────────────────────
  const [dualLayerData, setDualLayerData] = useState([]);
  const [calibrationData, setCalibrationData] = useState([]);
  const [cumulativeData, setCumulativeData] = useState([]);
  const [meterHealth, setMeterHealth] = useState({});
  const [survivalData, setSurvivalData] = useState({
    total: 0, caught_hmac: 0, caught_seq: 0,
    caught_ts: 0, caught_ml: 0, missed: 0
  });
  const [errorRateData, setErrorRateData] = useState([]);

  // Refs for accumulating data between state updates
  const dualLayerBucket = useRef({ crypto_only: 0, ml_only: 0, both_detected: 0, missed: 0, time: 0 });
  const bucketTimer = useRef(null);
  const cumulativeRef = useRef({ tp: 0, fp: 0, tn: 0, fn: 0, count: 0 });
  const errorBucket = useRef(null); // unused — errorRateData now computed from liveStats
  const startTimeRef = useRef(null);
  const lastProcessedPktRef = useRef(null);
  const meterHealthRef = useRef({});
  const survivalRef = useRef({ total: 0, caught_hmac: 0, caught_seq: 0, caught_ts: 0, caught_ml: 0, missed: 0 });
  const calibrationRef = useRef([]);
  const lastFloodTime = useRef({});

  const ws = useWebSocket('ws://localhost:8000/ws/dashboard');
  const sessInterval = useRef(null);

  // ── Process packet events for new analytics (all refs, no state deps) ──
  const processPacketForAnalytics = useCallback((pkt) => {
    const wasAttack = pkt.was_attack;
    const accepted = pkt.result === 'accepted';
    const mlFlagged = pkt.ml_flagged;
    const reason = (pkt.reason || '').toLowerCase();

    // --- Dual Layer tracking (ref only) ---
    // Flood dedup: a flood burst of 15-25 packets counts as ONE attack event
    if (wasAttack) {
      const attackType = pkt.attack_type || '';
      const meterId = pkt.meter_id;
      const now = Date.now();
      let isFloodDuplicate = false;

      if (attackType === 'flood') {
        const lastFlood = lastFloodTime.current[meterId] || 0;
        if (now - lastFlood < 500) {
          // Skip — subsequent packet in the same flood burst
          isFloodDuplicate = true;
        } else {
          lastFloodTime.current[meterId] = now;
          // Flood passes crypto, may be detected by ML
          if (accepted && mlFlagged) {
            dualLayerBucket.current.ml_only += 1;
          } else if (accepted && !mlFlagged) {
            dualLayerBucket.current.missed += 1;
          }
        }
      } else {
        // Replay and MITM: single packet per attack event
        if (!accepted && !mlFlagged) dualLayerBucket.current.crypto_only += 1;
        else if (accepted && mlFlagged) dualLayerBucket.current.ml_only += 1;
        else if (!accepted && mlFlagged) dualLayerBucket.current.both_detected += 1;
        else if (accepted && !mlFlagged) dualLayerBucket.current.missed += 1;
      }

      // --- Survival Funnel tracking (ref only, flushed by timer) ---
      // Use same flood dedup — only count first packet in burst
      if (!isFloodDuplicate) {
        const s = survivalRef.current;
        s.total += 1;
        if (!accepted) {
          if (reason.includes('hmac')) s.caught_hmac += 1;
          else if (reason.includes('replay') || reason.includes('sequence')) s.caught_seq += 1;
          else if (reason.includes('stale') || reason.includes('timestamp')) s.caught_ts += 1;
          else s.caught_hmac += 1;
        } else if (mlFlagged) {
          s.caught_ml += 1;
        } else {
          s.missed += 1;
        }
      }
    }

    // --- Cumulative Performance tracking (ref only) ---
    const c = cumulativeRef.current;
    c.count += 1;
    if (wasAttack && (!accepted || mlFlagged)) c.tp += 1;
    else if (!wasAttack && !accepted) c.fp += 1;
    else if (!wasAttack && accepted) c.tn += 1;
    else if (wasAttack && accepted && !mlFlagged) c.fn += 1;

    // --- Error Rate tracking: now computed server-side from liveStats (see liveStats useEffect)
    // No per-packet errorBucket update needed here.

    // --- Meter Health tracking (ref only, flushed by timer) ---
    const meterId = pkt.meter_id;
    if (meterId) {
      const mh = meterHealthRef.current;
      if (!mh[meterId]) mh[meterId] = { packets_sent: 0, accepted: 0, attacks: 0, total_attacks: 0, fp: 0, health_score: 100 };
      const m = mh[meterId];
      m.packets_sent += 1;
      if (accepted) m.accepted += 1;
      if (wasAttack) m.total_attacks += 1;                          // every attack, detected or not
      if (wasAttack && (!accepted || mlFlagged)) m.attacks += 1;   // detected attacks only
      if (!wasAttack && !accepted) m.fp += 1;
      // Health formula:
      //   FP penalty  : false positives hurt normal-traffic experience
      //   Miss penalty: attacks that slipped through ALL layers (fn per meter)
      const fpr      = m.packets_sent > 0 ? (m.fp / m.packets_sent) * 100 : 0;
      const missRate = m.total_attacks > 0 ? (m.total_attacks - m.attacks) / m.total_attacks : 0;
      m.health_score = Math.max(0, Math.min(100, 100 - (fpr * 2) - (missRate * 60)));
    }
  }, []); // No state dependencies — all tracking uses refs

  // ── 5-second bucket flush for ALL ref-tracked analytics ────────
  useEffect(() => {
    if (!isRunning) return;
    bucketTimer.current = setInterval(() => {
      const st = startTimeRef.current;
      const elapsed = st ? Math.floor((Date.now() - st.getTime()) / 1000) : 0;
      const timeLabel = `${Math.floor(elapsed / 60)}:${String(elapsed % 60).padStart(2, '0')}`;

      // Flush dual layer bucket — always flush for continuous chart data
      const b = dualLayerBucket.current;
      setDualLayerData(prev => {
        const point = { time: timeLabel, crypto_only: b.crypto_only, ml_only: b.ml_only, both_detected: b.both_detected, missed: b.missed };
        dualLayerBucket.current = { crypto_only: 0, ml_only: 0, both_detected: 0, missed: 0, time: elapsed };
        const next = [...prev, point];
        return next.length > 90 ? next.slice(-90) : next;
      });

      // errorRateData is now built from liveStats in the liveStats useEffect below — no flush needed here.

      // Flush survival data from ref to state
      const s = survivalRef.current;
      if (s.total > 0) {
        setSurvivalData({ ...s });
      }

      // Flush meter health from ref to state
      const mh = meterHealthRef.current;
      if (Object.keys(mh).length > 0) {
        setMeterHealth({ ...mh });
      }

      // Flush cumulative data
      const c = cumulativeRef.current;
      if (c.count > 0) {
        const precision = (c.tp + c.fp) > 0 ? (c.tp / (c.tp + c.fp)) * 100 : 100;
        setCumulativeData(prev => {
          const point = {
            time: timeLabel,
            cumulative_tp: c.tp,
            cumulative_fp: c.fp,
            precision: Math.round(precision * 10) / 10,
          };
          const next = [...prev, point];
          return next.length > 120 ? next.slice(-120) : next;
        });
      }

      // Flush calibration data from ref
      if (calibrationRef.current.length > 0) {
        setCalibrationData([...calibrationRef.current]);
      }
    }, 2000);
    return () => { if (bucketTimer.current) clearInterval(bucketTimer.current); };
  }, [isRunning]);

  // ── Process incoming packet events (full batch) ────────────────
  useEffect(() => {
    if (!isRunning || !ws.lastBatchRef) return;
    const batch = ws.lastBatchRef.current;
    if (batch && batch.length > 0) {
      for (let i = 0; i < batch.length; i++) {
        processPacketForAnalytics(batch[i]);
      }
    }
  }, [ws.packetBatchId, isRunning, processPacketForAnalytics]);

  // Build chart data points + errorRateData from live stats updates
  useEffect(() => {
    if (ws.liveStats && isRunning) {
      const elapsed = ws.liveStats.elapsed_seconds || 0;
      const timeLabel = `${Math.floor(elapsed / 60)}:${String(Math.floor(elapsed % 60)).padStart(2, '0')}`;
      setChartData(prev => {
        const point = {
          time: timeLabel,
          pps: ws.liveStats.throughput || 0,
          detectionRate: ws.liveStats.detection_accuracy || 0,
          throughput: ws.liveStats.throughput || 0,
          accepted: ws.liveStats.accepted || 0,
          rejected: ws.liveStats.rejected || 0,
          mlScore: ws.liveStats.ml_stats?.avg_score || 0,
          fpr: ws.liveStats.fpr || 0,
        };
        const next = [...prev, point];
        return next.length > 60 ? next.slice(-60) : next;
      });

      // Build errorRateData from authoritative server counters.
      // Server values are flood-deduped, so error_rate and attack_intensity
      // are independent — error_rate stays near 0 while attack_intensity fluctuates.
      const totalPkts = Math.max(ws.liveStats.total_packets || 1, 1);
      const injected  = ws.liveStats.attacks_injected   || 0;
      const fn        = ws.liveStats.false_negatives     || 0;
      const fp        = ws.liveStats.false_positives     || 0;
      setErrorRateData(prev => {
        const point = {
          time: timeLabel,
          error_rate: (fn + fp) / totalPkts,
          attack_intensity: injected / totalPkts,
        };
        const next = [...prev, point];
        return next.length > 60 ? next.slice(-60) : next;
      });
    }
  }, [ws.liveStats, isRunning]);

  // Build attack summary from attack log
  useEffect(() => {
    const log = ws.attackLog || [];
    const counts = { replay: 0, mitm: 0, flood: 0, unknown: 0 };
    log.forEach(a => {
      const t = (a.attack_type || 'unknown').toLowerCase();
      if (t in counts) counts[t] += 1;
      else counts.unknown += 1;
    });
    counts.total = log.length;
    setAttackSummary(counts);
  }, [ws.attackLog]);

  // Poll for active sessions while running
  useEffect(() => {
    if (isRunning) {
      const fetchSessions = () => {
        api.get('/api/sessions/active')
          .then(r => setSessions(r.data.active || []))
          .catch(() => {});
      };
      fetchSessions();
      sessInterval.current = setInterval(fetchSessions, 3000);
    } else {
      setSessions([]);
    }
    return () => { if (sessInterval.current) clearInterval(sessInterval.current); };
  }, [isRunning]);

  // When simulation_ended arrives via WS, mark as stopped
  useEffect(() => {
    if (ws.sessionMetrics) {
      setIsRunning(false);
      setStartTime(null);
    }
  }, [ws.sessionMetrics]);

  // Check running status on mount
  useEffect(() => {
    api.get('/api/stream/status')
      .then(r => {
        if (r.data.is_running) {
          setIsRunning(true);
          setNumMeters(r.data.num_meters || 100);
        }
      })
      .catch(() => {});
  }, []);

  // ── Accumulate ML calibration events in ref (flushed by timer) ─
  useEffect(() => {
    if (ws.calibrationEvent) {
      calibrationRef.current = [...calibrationRef.current, ws.calibrationEvent];
      if (calibrationRef.current.length > 200) calibrationRef.current = calibrationRef.current.slice(-200);
    }
  }, [ws.calibrationEvent]);

  const startSimulation = useCallback(async (meters) => {
    setLoading(true);
    try {
      ws.clearFeeds();
      ws.clearSessionMetrics();
      setChartData([]);
      setAttackSummary({ replay: 0, mitm: 0, flood: 0, unknown: 0, total: 0 });
      // Reset new analytics state
      setDualLayerData([]);
      setCalibrationData([]);
      setCumulativeData([]);
      setMeterHealth({});
      setSurvivalData({ total: 0, caught_hmac: 0, caught_seq: 0, caught_ts: 0, caught_ml: 0, missed: 0 });
      setErrorRateData([]);
      cumulativeRef.current = { tp: 0, fp: 0, tn: 0, fn: 0, count: 0 };
      dualLayerBucket.current = { crypto_only: 0, ml_only: 0, both_detected: 0, missed: 0, time: 0 };
      errorBucket.current = null; // errorRateData computed from liveStats — no bucket needed
      meterHealthRef.current = {};
      survivalRef.current = { total: 0, caught_hmac: 0, caught_seq: 0, caught_ts: 0, caught_ml: 0, missed: 0 };
      lastFloodTime.current = {};
      lastProcessedPktRef.current = null;

      const res = await api.post('/api/stream/start', { num_meters: meters });
      if (res.data.status === 'started') {
        setIsRunning(true);
        setNumMeters(meters);
        const now = new Date();
        setStartTime(now);
        startTimeRef.current = now;
      }
    } catch (e) {
      console.error('Start failed:', e);
    }
    setLoading(false);
  }, [ws]);

  const stopSimulation = useCallback(async () => {
    setLoading(true);
    try {
      await api.post('/api/stream/stop');
      setIsRunning(false);
      setStartTime(null);
      startTimeRef.current = null;
    } catch (e) {
      console.error('Stop failed:', e);
      setIsRunning(false);
      setStartTime(null);
      startTimeRef.current = null;
    }
    setLoading(false);
  }, []);

  const value = useMemo(() => ({
    // State
    isRunning, numMeters, setNumMeters, loading, startTime,
    // Actions
    startSimulation, stopSimulation,
    // WebSocket status
    wsConnected: ws.connected,
    // Live data from WebSocket
    liveStats: ws.liveStats,
    packetFeed: ws.packetFeed,
    attackLog: ws.attackLog,
    sessionMetrics: ws.sessionMetrics,
    // Derived data
    sessions,
    chartData,
    attackSummary,
    // NEW: Analytics chart data
    dualLayerData,
    calibrationData,
    cumulativeData,
    meterHealth,
    survivalData,
    errorRateData,
  }), [
    isRunning, numMeters, loading, startTime,
    startSimulation, stopSimulation,
    ws.connected, ws.liveStats, ws.packetFeed, ws.attackLog, ws.sessionMetrics,
    sessions, chartData, attackSummary,
    dualLayerData, calibrationData, cumulativeData, meterHealth, survivalData, errorRateData,
  ]);

  return (
    <SimulationContext.Provider value={value}>
      {children}
    </SimulationContext.Provider>
  );
}

export function useSimulation() {
  const ctx = useContext(SimulationContext);
  if (!ctx) throw new Error('useSimulation must be used within SimulationProvider');
  return ctx;
}
