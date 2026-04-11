import { apiRequest } from "./http";

export async function getAgents() {
  const res = await apiRequest("/api/agents");
  return res?.agents || [];
}

export async function getAgentStatus(id) {
  const res = await apiRequest("/api/agents");
  const list = res?.agents || [];
  return list.find((a) => Number(a.id) === Number(id)) || null;
}

export async function startAgent(id) {
  return apiRequest(`/api/agents/${id}/wake`, { method: "POST" });
}

export async function stopAgent(id) {
  return apiRequest(`/api/agents/${id}/hibernate`, { method: "POST" });
}
