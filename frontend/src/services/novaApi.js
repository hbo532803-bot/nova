import { apiRequest } from "./http";

export const fetchDashboard = () => apiRequest("/api/nova/dashboard");
export const fetchAgents = () => apiRequest("/api/agents");
export const fetchOpportunities = () => apiRequest("/api/opportunities");
export const fetchExecution = () => apiRequest("/api/commands?limit=100");
export const fetchLogs = () => apiRequest("/api/commands?limit=100");

export const runOpportunity = (id) => apiRequest(`/api/opportunities/${id}/convert`, { method: "POST" });
export const restartAgent = (id) => apiRequest(`/api/agents/${id}/wake`, { method: "POST" });
export const runExperiment = (id) => apiRequest(`/api/experiments/${id}/run`, { method: "POST" });
export const discoverOpportunities = () => apiRequest("/api/market/scan", { method: "POST" });
