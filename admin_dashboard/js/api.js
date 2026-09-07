// PSC App Update Manager - API client.
// This is the ONLY place the dashboard talks to the backend. It never
// touches Supabase directly and never holds a service-role key -
// everything is proxied through FastAPI using a short-lived JWT.

const API_BASE = window.PSC_API_BASE || "http://localhost:8000/api/v1";

function getToken() {
  return localStorage.getItem("psc_admin_token");
}

function setToken(token) {
  localStorage.setItem("psc_admin_token", token);
}

function clearToken() {
  localStorage.removeItem("psc_admin_token");
}

async function apiRequest(path, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401) {
    clearToken();
    window.location.href = "login.html";
    throw new Error("Not authenticated");
  }

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Request failed (${res.status})`);
  }

  if (res.status === 204) return null;
  return res.json();
}

const Api = {
  login: (email, password) =>
    apiRequest("/auth/login", { method: "POST", body: { email, password } }),
  me: () => apiRequest("/auth/me"),

  listApps: () => apiRequest("/apps"),
  createApp: (payload) => apiRequest("/apps", { method: "POST", body: payload }),
  updateApp: (id, payload) => apiRequest(`/apps/${id}`, { method: "PATCH", body: payload }),
  appReleaseHistory: (id) => apiRequest(`/apps/${id}/releases`),

  listReleases: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest(`/releases${qs ? `?${qs}` : ""}`);
  },
  createRelease: (payload) => apiRequest("/releases", { method: "POST", body: payload }),
  publishRelease: (id) => apiRequest(`/releases/${id}/publish`, { method: "POST" }),

  sendNotification: (payload) =>
    apiRequest("/notifications/send", { method: "POST", body: payload }),
  notificationHistory: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest(`/notifications/history${qs ? `?${qs}` : ""}`);
  },
};
