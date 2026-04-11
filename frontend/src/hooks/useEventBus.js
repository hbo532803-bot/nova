import { useEffect } from "react";
import { useNovaStore } from "../state/novaStore";
import { API_BASE_URL } from "../services/apiConfig";

export default function useEventBus() {
  const setLogs = useNovaStore((s) => s.setLogs);

  useEffect(() => {
    let ws;
    let alive = true;

    function push(event) {
      const current = useNovaStore.getState().logs || [];
      const next = [event, ...current].slice(0, 200);
      setLogs(next);
    }

    try {
      const token = localStorage.getItem("nova_token") || "";
      const qs = token ? `?token=${encodeURIComponent(token)}` : "";
      const wsBase = API_BASE_URL.replace(/^http/i, "ws");
      ws = new WebSocket(`${wsBase}/ws${qs}`);
      ws.onmessage = (msg) => {
        try {
          const event = JSON.parse(msg.data);
          if (!alive) return;
          push(event);
        } catch {
          // ignore
        }
      };
    } catch {
      // ignore
    }

    return () => {
      alive = false;
      try {
        ws?.close();
      } catch {
        // ignore
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}
