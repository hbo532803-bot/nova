const API = "http://localhost:8000/api/order";

async function request(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });

  if (!res.ok) {
    const details = await res.text();
    throw new Error(details || "Order API request failed");
  }

  return res.json();
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
