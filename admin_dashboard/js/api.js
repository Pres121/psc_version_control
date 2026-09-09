// PSC App Update Manager - API client.
// This is the ONLY place the dashboard talks to the backend. It never
// touches Supabase directly and never holds a service-role key -
// everything is proxied through FastAPI using a short-lived JWT.

const API_BASE = window.PSC_API_BASE || "https://psc-version-control.onrender.com/api/v1";

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
    throw new Error(formatApiError(data, res.status));
  }

  if (res.status === 204) return null;
  return res.json();
}

// FastAPI returns validation failures as an array of objects.  Converting that
// array directly to text produces "[object Object]", which gives admins no
// useful indication of what needs correcting.
function formatApiError(data, status) {
  const detail = data?.detail;
  if (typeof detail === "string" && detail.trim()) return detail;

  if (Array.isArray(detail)) {
    const messages = detail
      .map((issue) => {
        if (typeof issue === "string") return issue;
        if (!issue || typeof issue !== "object") return null;
        const field = Array.isArray(issue.loc)
          ? issue.loc.filter((part) => part !== "body").join(" → ")
          : "";
        return field ? `${field}: ${issue.msg || "Invalid value"}` : issue.msg;
      })
      .filter(Boolean);
    if (messages.length) return messages.join(". ");
  }

  if (detail && typeof detail === "object") {
    return detail.message || detail.error || `Request failed (${status})`;
  }
  return data?.message || `Request failed (${status})`;
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
  updateRelease: (id, payload) => apiRequest(`/releases/${id}`, { method: "PATCH", body: payload }),
  publishRelease: (id, verification) => apiRequest(`/releases/${id}/publish`, { method: "POST", body: verification }),
  unpublishRelease: (id, verification) => apiRequest(`/releases/${id}/unpublish`, { method: "POST", body: verification }),
  deleteRelease: (id, verification) => apiRequest(`/releases/${id}`, { method: "DELETE", body: verification }),

  sendNotification: (payload) =>
    apiRequest("/notifications/send", { method: "POST", body: payload }),
  notificationHistory: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest(`/notifications/history${qs ? `?${qs}` : ""}`);
  },
};
