const envApiUrl =
  (typeof import.meta !== "undefined" && import.meta.env && (import.meta.env.VITE_API_URL || import.meta.env.REACT_APP_API_URL)) || "";

export const API_BASE_URL = (envApiUrl || "http://127.0.0.1:8000").replace(/\/$/, "");

export const WS_BASE_URL = API_BASE_URL.replace(/^http:/i, "ws:").replace(/^https:/i, "wss:");
