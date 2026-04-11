import { apiRequest } from "./http";

export async function getExperiments() {
  const data = await apiRequest("/api/experiments");
  return data?.experiments || [];
}

export async function runExperiment(data) {
  const id = data?.id;
  if (!id) throw new Error("Experiment id is required");
  return apiRequest(`/api/experiments/${id}/run`, { method: "POST" });
}

export async function stopExperiment(id) {
  return apiRequest("/api/commands", {
    method: "POST",
    body: JSON.stringify({ text: `stop experiment ${id}` })
  });
}
