const API = "http://localhost:8000/api";

export async function getOpportunities() {
  const res = await fetch(`${API}/opportunities`);
  return res.json();
}

export async function getOpportunity(id) {
  const res = await fetch(`${API}/opportunities/${id}`);
  return res.json();
}

export async function createOpportunity(data) {
  const res = await fetch(`${API}/opportunities`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  return res.json();
}