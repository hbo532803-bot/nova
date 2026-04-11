import { apiRequest } from "./http";

export function getStoredToken() {
  return localStorage.getItem("nova_token") || "";
}

export function parseJwt(token) {
  try {
    const payload = token.split(".")[1];
    const decoded = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

export function isTokenExpired(token) {
  if (!token) return true;
  const payload = parseJwt(token);
  const exp = Number(payload?.exp || 0);
  if (!exp) return false;
  return Date.now() >= exp * 1000;
}

export async function validateStoredSession() {
  const token = getStoredToken();
  if (!token || isTokenExpired(token)) {
    localStorage.removeItem("nova_token");
    return { valid: false, reason: "missing_or_expired" };
  }

  try {
    await apiRequest("/api/system/state", { auth: true });
    return { valid: true, reason: "ok" };
  } catch {
    localStorage.removeItem("nova_token");
    return { valid: false, reason: "invalid" };
  }
}
