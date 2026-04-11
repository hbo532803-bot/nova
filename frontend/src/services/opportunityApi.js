import { apiRequest } from "./http";

export async function getOpportunities() {
  const data = await apiRequest("/api/opportunities");
  return data?.proposals || [];
}

export async function getOpportunity(id) {
  const list = await getOpportunities();
  return list.find((o) => Number(o.id) === Number(id)) || null;
}

export async function createOpportunity(data) {
  return apiRequest("/api/commands", {
    method: "POST",
    body: JSON.stringify({ text: `research ${data?.name || "opportunity"}` })
  });
}
