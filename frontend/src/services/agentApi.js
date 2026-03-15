const API = "http://localhost:8000/api";

export async function getAgents() {
  const res = await fetch(`${API}/agents`);
  return res.json();
}

export async function getAgentStatus(id) {
  const res = await fetch(`${API}/agents/${id}/status`);
  return res.json();
}

export async function startAgent(id) {
  const res = await fetch(`${API}/agents/${id}/start`, {
    method: "POST"
  });
  return res.json();
}

export async function stopAgent(id) {
  const res = await fetch(`${API}/agents/${id}/stop`, {
    method: "POST"
  });
  return res.json();
}