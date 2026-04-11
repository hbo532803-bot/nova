import { API_BASE_URL } from "./apiConfig";

const API = `${API_BASE_URL}/api`;

export async function getSocialConsole() {
  const res = await fetch(`${API}/social/console`);
  return res.json();
}

export async function generateSocialContent(progress_update = "") {
  const res = await fetch(`${API}/social/content/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ progress_update, limit: 6 })
  });
  return res.json();
}

export async function updateSocialContentStatus(contentId, status) {
  const res = await fetch(`${API}/social/content/${contentId}/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status })
  });
  return res.json();
}

export async function updateSocialReplyStatus(queueId, status) {
  const res = await fetch(`${API}/social/replies/${queueId}/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status })
  });
  return res.json();
}
