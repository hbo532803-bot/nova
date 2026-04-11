import { useEffect, useRef } from "react";
import { useNovaStore } from "../state/novaStore";
import { WS_BASE_URL } from "../services/apiConfig";
import { getStoredToken, isTokenExpired } from "../services/auth";

export default function useEventBus() {
  const setLogs = useNovaStore((s) => s.setLogs);
  const setRealtimeConnected = useNovaStore((s) => s.setRealtimeConnected);
  const setRealtimeFallback = useNovaStore((s) => s.setRealtimeFallback);
  const wsRef = useRef(null);
  const retryTimerRef = useRef(null);
  const retryAttemptRef = useRef(0);
  const aliveRef = useRef(false);
  const connectingRef = useRef(false);

  useEffect(() => {
    aliveRef.current = true;

    function push(event) {
      const current = useNovaStore.getState().logs || [];
      const next = [event, ...current].slice(0, 200);
      setLogs(next);
    }

    function clearRetryTimer() {
      if (retryTimerRef.current) {
        clearTimeout(retryTimerRef.current);
        retryTimerRef.current = null;
      }
    }

    function closeCurrentSocket() {
      const socket = wsRef.current;
      wsRef.current = null;
      if (!socket) return;
      try {
        socket.close();
      } catch {
        // ignore
      }
    }

    function scheduleReconnect() {
      if (!aliveRef.current) return;
      clearRetryTimer();
      retryAttemptRef.current += 1;
      const delayMs = Math.min(30000, 1000 * 2 ** Math.min(retryAttemptRef.current, 5));
      retryTimerRef.current = setTimeout(connect, delayMs);
      console.info("[event-bus] reconnect scheduled", { attempt: retryAttemptRef.current, delayMs });
    }

    function connect() {
      if (!aliveRef.current || connectingRef.current) return;
      const token = getStoredToken();
      if (!token || isTokenExpired(token)) {
        setRealtimeFallback(true);
        setRealtimeConnected(false);
        scheduleReconnect();
        return;
      }

      try {
        clearRetryTimer();
        closeCurrentSocket();
        connectingRef.current = true;
        const wsUrl = `${WS_BASE_URL}/ws?token=${encodeURIComponent(token)}`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;
        console.info("[event-bus] connecting", { wsUrl });
        ws.onopen = () => {
          if (!aliveRef.current) return;
          connectingRef.current = false;
          retryAttemptRef.current = 0;
          setRealtimeConnected(true);
          setRealtimeFallback(false);
          console.info("[event-bus] connected");
        };
        ws.onmessage = (msg) => {
          try {
            const event = JSON.parse(msg.data);
            if (!aliveRef.current) return;
            push(event);
          } catch {
            // ignore malformed event
          }
        };
        ws.onclose = (event) => {
          connectingRef.current = false;
          setRealtimeConnected(false);
          if (!aliveRef.current) return;
          setRealtimeFallback(true);
          console.warn("[event-bus] disconnected", { code: event.code, reason: event.reason || "n/a" });
          scheduleReconnect();
        };
        ws.onerror = (event) => {
          if (!aliveRef.current) return;
          setRealtimeFallback(true);
          console.error("[event-bus] error", event);
        };
      } catch {
        connectingRef.current = false;
        setRealtimeConnected(false);
        setRealtimeFallback(true);
        scheduleReconnect();
      }
    }
    connect();

    return () => {
      aliveRef.current = false;
      connectingRef.current = false;
      clearRetryTimer();
      closeCurrentSocket();
    };
  }, [setLogs, setRealtimeConnected, setRealtimeFallback]);
}
