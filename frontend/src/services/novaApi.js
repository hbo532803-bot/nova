import { apiRequest as request } from "./http";

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
