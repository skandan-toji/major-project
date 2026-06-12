import { useState, useEffect, useRef, useCallback } from 'react';

export function useWebSocket(url) {
  const [connected, setConnected] = useState(false);
  const [packetFeed, setPacketFeed] = useState([]);
  const [attackLog, setAttackLog] = useState([]);
  const [liveStats, setLiveStats] = useState(null);
  const [sessionMetrics, setSessionMetrics] = useState(null);
  const [calibrationEvent, setCalibrationEvent] = useState(null);
  // Batch counter — increments on each flush so consumers know new data arrived
  const [packetBatchId, setPacketBatchId] = useState(0);
  const wsRef = useRef(null);
  const reconnectRef = useRef(null);

  // ── Batching buffers to throttle React state updates ──────────
  const packetBuf = useRef([]);
  const attackBuf = useRef([]);
  const lastBatchRef = useRef([]);  // The most recent batch of new packets
  const flushRef = useRef(null);

  // Flush buffered events to React state every 250ms
  useEffect(() => {
    flushRef.current = setInterval(() => {
      if (packetBuf.current.length > 0) {
        const batch = [...packetBuf.current];
        packetBuf.current = [];
        lastBatchRef.current = batch;
        setPacketFeed(prev => [...batch, ...prev].slice(0, 100));
        setPacketBatchId(id => id + 1);
      }
      if (attackBuf.current.length > 0) {
        const batch = [...attackBuf.current];
        attackBuf.current = [];
        setAttackLog(prev => [...batch, ...prev].slice(0, 50000));
      }
    }, 250);
    return () => { if (flushRef.current) clearInterval(flushRef.current); };
  }, []);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        if (reconnectRef.current) {
          clearTimeout(reconnectRef.current);
          reconnectRef.current = null;
        }
      };

      ws.onclose = () => {
        setConnected(false);
        reconnectRef.current = setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        ws.close();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          switch (data.event_type) {
            case 'packet':
              packetBuf.current.push(data);
              break;
            case 'attack':
              attackBuf.current.push(data);
              break;
            case 'stats':
              setLiveStats(data);
              break;
            case 'simulation_ended':
              setSessionMetrics(data.metrics);
              break;
            case 'ml_calibration':
              setCalibrationEvent(data);
              break;
            default:
              break;
          }
        } catch (e) {
          // ignore parse errors
        }
      };
    } catch (e) {
      reconnectRef.current = setTimeout(connect, 3000);
    }
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
    };
  }, [connect]);

  const clearSessionMetrics = useCallback(() => setSessionMetrics(null), []);
  const clearFeeds = useCallback(() => {
    setPacketFeed([]);
    setAttackLog([]);
    setLiveStats(null);
    setCalibrationEvent(null);
    packetBuf.current = [];
    attackBuf.current = [];
    lastBatchRef.current = [];
    setPacketBatchId(0);
  }, []);

  return {
    connected, packetFeed, attackLog,
    liveStats, sessionMetrics, calibrationEvent,
    packetBatchId, lastBatchRef,
    clearSessionMetrics, clearFeeds
  };
}
