import { apiRequest } from "./http";

export async function getSocialConsole() {
  return apiRequest("/api/social/console");
}

export async function generateSocialContent(progress_update = "") {
  return apiRequest("/api/social/content/generate", {
    method: "POST",
    body: JSON.stringify({ progress_update, limit: 6 })
  });
}

export async function updateSocialContentStatus(contentId, status) {
  return apiRequest(`/api/social/content/${contentId}/status`, {
    method: "POST",
    body: JSON.stringify({ status })
  });
}

export async function updateSocialReplyStatus(queueId, status) {
  return apiRequest(`/api/social/replies/${queueId}/status`, {
    method: "POST",
    body: JSON.stringify({ status })
  });
}

export async function convertSocialLead(leadId, amount) {
  return apiRequest(`/api/social/leads/${leadId}/convert`, {
    method: "POST",
    body: JSON.stringify({ amount, response_state: "accepted" })
  });
}
