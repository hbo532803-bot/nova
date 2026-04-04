import { API_BASE_URL } from "./apiConfig";

const API = API_BASE_URL;

function token() {
  return localStorage.getItem("nova_token");
}

async function request(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token()}`,
      ...(options.headers || {})
    }
  });

  if (res.status === 401) {
    localStorage.removeItem("nova_token");
    window.location = "/login";
    return;
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || "API request failed");
  }

  return res.json();
}

export function getSystemState(options) {
  return request("/api/system/state", options);
}

export function getConfidence(options) {
  return request("/api/confidence", options);
}

export function listAgents(status, options) {
  const qs = status ? `?status=${encodeURIComponent(status)}` : "";
  return request(`/api/agents${qs}`, options);
}

export function listOpportunities(options) {
  return request("/api/opportunities", options);
}

export function listExperiments(options) {
  return request("/api/experiments", options);
}

export function listPlaybooks(options) {
  return request("/api/playbooks", options);
}

export function attachPlaybook(experimentId, playbookName, options) {
  return request(`/api/experiments/${experimentId}/playbooks/${encodeURIComponent(playbookName)}/attach`, {
    method: "POST",
    ...(options || {})
  });
}

export function strategyLearn(options) {
  return request("/api/strategy/learn", { method: "POST", ...(options || {}) });
}

export function getExperimentAnalytics(limit = 50, options) {
  return request(`/api/analytics/experiments?limit=${limit}`, options);
}

export function getAgentActivity(limit = 200, options) {
  return request(`/api/analytics/agents/activity?limit=${limit}`, options);
}

export function getConfidenceTrend(limit = 50, options) {
  return request(`/api/analytics/confidence/trend?limit=${limit}`, options);
}

export function getStabilityHealth(options) {
  return request("/api/system/stability/health", options);
}

export function recoverSystem(options) {
  return request("/api/system/stability/recover", { method: "POST", ...(options || {}) });
}

export function getAgentProductivity(days = 7, options) {
  return request(`/api/analytics/agents/productivity?days=${days}`, options);
}

export function getKnowledgeGraphSummary(options) {
  return request("/api/knowledge/graph/summary", options);
}

export function getPortfolioHealth(options) {
  return request("/api/analytics/portfolio/health", options);
}

export function getCurrentStrategy(options) {
  return request("/api/analytics/strategy/current", options);
}

export function getKnowledgeInsights(options) {
  return request("/api/knowledge/insights", options);
}

export function getCognitiveLast(options) {
  return request("/api/cognitive/last", options);
}

export function getResearchLast(options) {
  return request("/api/research/last", options);
}

export function evolveAgents(options) {
  return request("/api/agents/factory/evolve", { method: "POST", ...(options || {}) });
}

export function listReflections(limit = 50, options) {
  return request(`/api/learning/reflections?limit=${limit}`, options);
}

export function submitCommand(text, options) {
  return request("/api/commands", {
    method: "POST",
    body: JSON.stringify({ text }),
    ...(options || {})
  });
}

export function listCommands(limit = 50, options) {
  return request(`/api/commands?limit=${limit}`, options);
}

export function marketScan(options) {
  return request("/api/market/scan", { method: "POST", ...(options || {}) });
}

export function approveOpportunity(id, options) {
  return request(`/api/opportunities/${id}/approve`, { method: "POST", ...(options || {}) });
}

export function rejectOpportunity(id, options) {
  return request(`/api/opportunities/${id}/reject`, { method: "POST", ...(options || {}) });
}

export function convertOpportunity(id, options) {
  return request(`/api/opportunities/${id}/convert`, { method: "POST", ...(options || {}) });
}

export function runExperimentById(id, options) {
  return request(`/api/experiments/${id}/run`, { method: "POST", ...(options || {}) });
}

export function hibernateAgent(id, options) {
  return request(`/api/agents/${id}/hibernate`, { method: "POST", ...(options || {}) });
}

export function wakeAgent(id, options) {
  return request(`/api/agents/${id}/wake`, { method: "POST", ...(options || {}) });
}

