import { API_BASE_URL } from "./apiConfig";

const API = `${API_BASE_URL}/api`;

export async function getExecutionPlan(id) {
  const res = await fetch(`${API}/execution/${id}`);
  return res.json();
}

export async function startExecution(id) {
  const res = await fetch(`${API}/execution/${id}/start`, {
    method: "POST"
  });

  return res.json();
}

export async function stopExecution(id) {
  const res = await fetch(`${API}/execution/${id}/stop`, {
    method: "POST"
  });

  return res.json();
}