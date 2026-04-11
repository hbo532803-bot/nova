import { API_BASE_URL } from "./apiConfig";

export async function apiRequest(path, options = {}) {
  const token = localStorage.getItem("nova_token");
  const headers = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(options.headers || {})
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers
  });

  if (res.status === 401) {
    localStorage.removeItem("nova_token");
    if (window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }

  const isJson = (res.headers.get("content-type") || "").includes("application/json");
  const payload = isJson ? await res.json().catch(() => ({})) : await res.text().catch(() => "");

  if (!res.ok) {
    throw new Error((payload && payload.detail) || payload || "API request failed");
  }

  return payload;
}
