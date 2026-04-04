const API = (import.meta.env.VITE_API_BASE || "http://localhost:8000").replace(/\/$/, "");

function token() {
  return localStorage.getItem("nova_token");
}

async function request(url, options = {}) {
  const authToken = token();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`;
  }

  const res = await fetch(`${API}${url}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    localStorage.removeItem("nova_token");
    window.location = "/login";
    return;
  }

  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    throw new Error(payload.detail || "API request failed");
  }

  return res.json();
}

export function fetchDashboard() {
  return request("/api/nova/dashboard");
}

export function fetchAgents() {
  return request("/api/nova/agents");
}

export function fetchOpportunities() {
  return request("/api/nova/opportunities");
}

export function fetchExecution() {
  return request("/api/nova/execution");
}

export function fetchLogs() {
  return request("/api/nova/logs");
}

export function runOpportunity(id) {
  return request(`/api/nova/opportunity/${id}/execute`, {
    method: "POST",
  });
}

export function restartAgent(id) {
  return request(`/api/nova/agent/${id}/restart`, {
    method: "POST",
  });
}

export function runExperiment(id) {
  return request(`/api/nova/experiment/${id}/run`, {
    method: "POST",
  });
}

export function discoverOpportunities() {
  return request("/api/nova/opportunity/discover", {
    method: "POST",
  });
}
