import { apiRequest } from "./http";

function request(path, options) {
  return apiRequest(path, options);
}

export const getSystemState = (options) => request("/api/system/state", options);
export const getConfidence = (options) => request("/api/confidence", options);
export const listAgents = (status, options) => request(`/api/agents${status ? `?status=${encodeURIComponent(status)}` : ""}`, options);
export const listOpportunities = (options) => request("/api/opportunities", options);
export const listExperiments = (options) => request("/api/experiments", options);
export const listPlaybooks = (options) => request("/api/playbooks", options);
export const attachPlaybook = (experimentId, playbookName, options) =>
  request(`/api/experiments/${experimentId}/playbooks/${encodeURIComponent(playbookName)}/attach`, { method: "POST", ...(options || {}) });
export const strategyLearn = (options) => request("/api/strategy/learn", { method: "POST", ...(options || {}) });
export const getExperimentAnalytics = (limit = 50, options) => request(`/api/analytics/experiments?limit=${limit}`, options);
export const getAgentActivity = (limit = 200, options) => request(`/api/analytics/agents/activity?limit=${limit}`, options);
export const getConfidenceTrend = (limit = 50, options) => request(`/api/analytics/confidence/trend?limit=${limit}`, options);
export const getStabilityHealth = (options) => request("/api/system/stability/health", options);
export const recoverSystem = (options) => request("/api/system/stability/recover", { method: "POST", ...(options || {}) });
export const getAgentProductivity = (days = 7, options) => request(`/api/analytics/agents/productivity?days=${days}`, options);
export const getKnowledgeGraphSummary = (options) => request("/api/knowledge/graph/summary", options);
export const getPortfolioHealth = (options) => request("/api/analytics/portfolio/health", options);
export const getCurrentStrategy = (options) => request("/api/analytics/strategy/current", options);
export const getKnowledgeInsights = (options) => request("/api/knowledge/insights", options);
export const getCognitiveLast = (options) => request("/api/cognitive/last", options);
export const getResearchLast = (options) => request("/api/research/last", options);
export const evolveAgents = (options) => request("/api/agents/factory/evolve", { method: "POST", ...(options || {}) });
export const listReflections = (limit = 50, options) => request(`/api/learning/reflections?limit=${limit}`, options);
export const submitCommand = (text, options) => request("/api/commands", { method: "POST", body: JSON.stringify({ text }), ...(options || {}) });
export const listCommands = (limit = 50, options) => request(`/api/commands?limit=${limit}`, options);
export const marketScan = (options) => request("/api/market/scan", { method: "POST", ...(options || {}) });
export const approveOpportunity = (id, options) => request(`/api/opportunities/${id}/approve`, { method: "POST", ...(options || {}) });
export const rejectOpportunity = (id, options) => request(`/api/opportunities/${id}/reject`, { method: "POST", ...(options || {}) });
export const convertOpportunity = (id, options) => request(`/api/opportunities/${id}/convert`, { method: "POST", ...(options || {}) });
export const runExperimentById = (id, options) => request(`/api/experiments/${id}/run`, { method: "POST", ...(options || {}) });
export const hibernateAgent = (id, options) => request(`/api/agents/${id}/hibernate`, { method: "POST", ...(options || {}) });
export const wakeAgent = (id, options) => request(`/api/agents/${id}/wake`, { method: "POST", ...(options || {}) });
