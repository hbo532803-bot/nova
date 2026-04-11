import { apiRequest } from "./http";

async function request(path, options = {}) {
  return apiRequest(`/api/order${path}`, { auth: false, ...options });
}

export function createOrder(input, details = {}) {
  return request("/create", {
    method: "POST",
    body: JSON.stringify({ input, details })
  });
}

export function confirmOrder(orderId, selectedPlan) {
  return request("/confirm", {
    method: "POST",
    body: JSON.stringify({ order_id: orderId, selected_plan: selectedPlan })
  });
}

export function fetchOrderStatus(orderId) {
  return request(`/status/${orderId}`);
}
