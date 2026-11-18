let csrfToken = "";

async function request(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const response = await fetch(path, {
    ...options,
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(csrfToken && !["GET", "HEAD", "OPTIONS"].includes(method)
        ? { "X-CSRF-Token": csrfToken }
        : {}),
      ...options.headers,
    },
  });
  const contentType = response.headers.get("Content-Type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : { error: `The server returned an unexpected response (${response.status}).` };
  if (!response.ok) {
    const error = new Error(payload.error || `Request failed (${response.status}).`);
    error.status = response.status;
    throw error;
  }
  if (payload.csrf_token) csrfToken = payload.csrf_token;
  if (path === "/api/auth/logout") csrfToken = "";
  return payload;
}

function jsonBody(value) {
  return JSON.stringify(value);
}

export const api = {
  health: () => request("/api/health"),
  csrf: () => request("/api/auth/csrf"),
  me: () => request("/api/auth/me"),
  login: (identifier, password) =>
    request("/api/auth/login", { method: "POST", body: jsonBody({ identifier, password }) }),
  register: (data) =>
    request("/api/auth/register", { method: "POST", body: jsonBody(data) }),
  logout: () => request("/api/auth/logout", { method: "POST" }),
  categories: () => request("/api/categories"),
  dashboard: (userId) => request(`/api/dashboard?user_id=${encodeURIComponent(userId)}`),
  catalog: (userId, filters = {}) => {
    const params = new URLSearchParams({ user_id: String(userId), ...filters });
    return request(`/api/catalog?${params}`);
  },
  savedItems: (userId) => request(`/api/users/${userId}/saved-items`),
  interests: (userId) => request(`/api/users/${userId}/interests`),
  history: (userId) => request(`/api/history?user_id=${encodeURIComponent(userId)}`),
  saveItem: (userId, itemId) =>
    request(`/api/users/${userId}/saved-items/${itemId}`, { method: "POST" }),
  unsaveItem: (userId, itemId) =>
    request(`/api/users/${userId}/saved-items/${itemId}`, { method: "DELETE" }),
  rateItem: (userId, itemId, rating) =>
    request(`/api/users/${userId}/ratings`, {
      method: "POST",
      body: jsonBody({ item_id: itemId, rating }),
    }),
  recordInteraction: (userId, itemId, interactionType) =>
    request(`/api/users/${userId}/interactions`, {
      method: "POST",
      body: jsonBody({ item_id: itemId, interaction_type: interactionType }),
    }),
  updateInterests: (userId, interests) =>
    request(`/api/users/${userId}/interests`, {
      method: "PUT",
      body: jsonBody({ interests }),
    }),
};
