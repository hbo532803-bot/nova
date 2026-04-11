import { apiRequest } from "./http";

export async function getAgents() {
  return apiRequest("/api/agents");
}

export async function getAgentStatus(id) {
  return apiRequest(`/api/agents/${id}/status`);
}

export async function startAgent(id) {
  return apiRequest(`/api/agents/${id}/start`, {
    method: "POST"
  });
}

export async function stopAgent(id) {
  return apiRequest(`/api/agents/${id}/stop`, {
    method: "POST"
  });
}
