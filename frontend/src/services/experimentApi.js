import { apiRequest } from "./http";

export async function getExperiments() {
  return apiRequest("/api/experiments");
}

export async function runExperiment(data) {
  return apiRequest("/api/experiments/run", {
    method: "POST",
    body: JSON.stringify(data)
  });
}

export async function stopExperiment(id) {
  return apiRequest(`/api/experiments/${id}/stop`, {
    method: "POST"
  });
}
