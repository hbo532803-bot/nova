import { API_BASE_URL } from "./apiConfig";

const API = `${API_BASE_URL}/api`;

export async function getExperiments() {
  const res = await fetch(`${API}/experiments`);
  return res.json();
}

export async function runExperiment(data) {
  const res = await fetch(`${API}/experiments/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  });

  return res.json();
}

export async function stopExperiment(id) {
  const res = await fetch(`${API}/experiments/${id}/stop`, {
    method: "POST"
  });

  return res.json();
}