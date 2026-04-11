import { apiRequest } from "./http";

export async function getExecutionPlan(id) {
  const data = await apiRequest("/api/commands?limit=200");
  const commands = data?.commands || [];
  return commands.find((c) => Number(c.id) === Number(id)) || null;
}

export async function startExecution(id) {
  return apiRequest("/api/commands", {
    method: "POST",
    body: JSON.stringify({ text: `run command ${id}` })
  });
}

export async function stopExecution(id) {
  return apiRequest("/api/commands", {
    method: "POST",
    body: JSON.stringify({ text: `stop command ${id}` })
  });
}
