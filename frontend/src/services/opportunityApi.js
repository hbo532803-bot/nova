import { apiRequest } from "./http";

export async function getOpportunities() {
  return apiRequest("/api/opportunities");
}

export async function getOpportunity(id) {
  return apiRequest(`/api/opportunities/${id}`);
}

export async function createOpportunity(data) {
  return apiRequest("/api/opportunities", {
    method: "POST",
    body: JSON.stringify(data)
  });
}
