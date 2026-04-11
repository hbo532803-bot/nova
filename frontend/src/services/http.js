import { API_BASE_URL } from "./apiConfig";

export async function apiRequest(path, options = {}) {
  const { auth = true, ...requestOptions } = options;
  const token = localStorage.getItem("nova_token");
  if (auth && !token) {
    throw new Error("Session expired, please login again");
  }
  const headers = {
    ...(requestOptions.body ? { "Content-Type": "application/json" } : {}),
    ...(requestOptions.headers || {})
  };

  if (auth && token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let res;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...requestOptions,
      headers
    });
  } catch (error) {
    if (error?.name === "AbortError") {
      throw error;
    }
    throw new Error(error?.message || "Network request failed");
  }

  if (res.status === 401) {
    localStorage.removeItem("nova_token");
    sessionStorage.setItem("nova_auth_message", "Session expired, please login again");
    if (window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
    throw new Error("Session expired, please login again");
  }

  const isJson = (res.headers.get("content-type") || "").includes("application/json");
  const payload = isJson ? await res.json().catch(() => ({})) : await res.text().catch(() => "");

  if (!res.ok) {
    throw new Error((payload && payload.detail) || payload || "API request failed");
  }

  return payload;
}
