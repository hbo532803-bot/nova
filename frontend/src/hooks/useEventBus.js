import { useEffect } from "react";
import { useNovaStore } from "../state/novaStore";
import { API_BASE_URL } from "../services/apiConfig";
import { getStoredToken, isTokenExpired } from "../services/auth";

export default function useEventBus() {
  const setLogs = useNovaStore((s) => s.setLogs);
  const setRealtimeConnected = useNovaStore((s) => s.setRealtimeConnected);
  const setRealtimeFallback = useNovaStore((s) => s.setRealtimeFallback);

  useEffect(() => {
    let ws;
    let alive = true;
    let retryTimer;

    function push(event) {
      const current = useNovaStore.getState().logs || [];
      const next = [event, ...current].slice(0, 200);
      setLogs(next);
    }

    function connect() {
      const token = getStoredToken();
      if (!token || isTokenExpired(token)) {
        setRealtimeFallback(true);
        setRealtimeConnected(false);
        return;
      }

      try {
      const qs = token ? `?token=${encodeURIComponent(token)}` : "";
      const wsBase = API_BASE_URL.replace(/^http/i, "ws");
      ws = new WebSocket(`${wsBase}/ws${qs}`);
      ws.onopen = () => {
        setRealtimeConnected(true);
        setRealtimeFallback(false);
      };
      ws.onmessage = (msg) => {
        try {
          const event = JSON.parse(msg.data);
          if (!alive) return;
          push(event);
        } catch {
          // ignore
        }
      };
      ws.onclose = () => {
        setRealtimeConnected(false);
        if (!alive) return;
        setRealtimeFallback(true);
        retryTimer = setTimeout(connect, 5000);
      };
      ws.onerror = () => {
        setRealtimeFallback(true);
      };
      } catch {
        setRealtimeConnected(false);
        setRealtimeFallback(true);
      }
    }
    connect();

    return () => {
      alive = false;
      clearTimeout(retryTimer);
      try {
        ws?.close();
      } catch {
        // ignore
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}
