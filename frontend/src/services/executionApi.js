import { apiRequest } from "./http";

export async function getExecutionPlan(id) {
  return apiRequest(`/api/execution/${id}`);
}

export async function startExecution(id) {
  return apiRequest(`/api/execution/${id}/start`, {
    method: "POST"
  });
}

export async function stopExecution(id) {
  return apiRequest(`/api/execution/${id}/stop`, {
    method: "POST"
  });
}
