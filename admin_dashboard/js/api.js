// PSC App Update Manager - API client.
// Admin JWT goes to FastAPI only. Large APK/IPA binaries upload directly to
// Supabase Storage using short-lived signed URLs minted by the backend —
// the dashboard never holds a service-role key.

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

async function uploadReleaseBinaryDirect(releaseId, file, onProgress) {
  const report = (percent, label) => {
    if (typeof onProgress === "function") onProgress(percent, label);
  };

  report(0, "Preparing upload…");
  const plan = await apiRequest(`/releases/${releaseId}/upload-url`, {
    method: "POST",
    body: {
      file_name: file.name,
      file_size_bytes: file.size,
    },
  });

  const targets = plan.uploads || [];
  const totalBytes = Math.max(file.size, 1) * Math.max(targets.length, 1);

  for (let i = 0; i < targets.length; i++) {
    const target = targets[i];
    const form = new FormData();
    form.append("cacheControl", "3600");
    form.append("", file, file.name);
    const baseLoaded = file.size * i;
    const label =
      targets.length > 1
        ? `Uploading to storage (${i + 1}/${targets.length})…`
        : "Uploading to storage…";

    await putSignedUpload(target.signed_url, form, (loaded) => {
      const overall = Math.min(99, Math.round(((baseLoaded + loaded) / totalBytes) * 100));
      report(overall, label);
    });
  }

  report(99, "Finalizing…");
  const result = await apiRequest(`/releases/${releaseId}/upload-complete`, {
    method: "POST",
    body: {
      storage_path: plan.storage_path,
      file_name: plan.file_name,
      file_size_bytes: plan.file_size_bytes,
    },
  });
  report(100, "Upload complete");
  return result;
}

function putSignedUpload(url, form, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", url);
    xhr.setRequestHeader("x-upsert", "true");
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && typeof onProgress === "function") {
        onProgress(event.loaded, event.total);
      }
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
        return;
      }
      const text = (xhr.responseText || "").slice(0, 200);
      reject(
        new Error(
          text
            ? `Direct upload to storage failed (${xhr.status}): ${text}`
            : `Direct upload to storage failed (${xhr.status})`
        )
      );
    };
    xhr.onerror = () => reject(new Error("Network error during direct upload"));
    xhr.onabort = () => reject(new Error("Upload aborted"));
    xhr.send(form);
  });
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
  verifyOtp: (challengeToken, otp) =>
    apiRequest("/auth/verify-otp", {
      method: "POST",
      body: { challenge_token: challengeToken, otp },
    }),
  me: () => apiRequest("/auth/me"),
  listAdmins: () => apiRequest("/auth/admins"),
  createAdmin: (payload) => apiRequest("/auth/admins", { method: "POST", body: payload }),
  updateAdmin: (id, payload) => apiRequest(`/auth/admins/${id}`, { method: "PATCH", body: payload }),

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
  uploadReleaseBinary: (id, file, onProgress) => uploadReleaseBinaryDirect(id, file, onProgress),

  sendNotification: (payload) =>
    apiRequest("/notifications/send", { method: "POST", body: payload }),
  notificationHistory: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest(`/notifications/history${qs ? `?${qs}` : ""}`);
  },

  listLogs: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest(`/logs${qs ? `?${qs}` : ""}`);
  },

  createAnnouncement: (payload) =>
    apiRequest("/announcements", { method: "POST", body: payload }),
  listAnnouncements: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest(`/announcements${qs ? `?${qs}` : ""}`);
  },
};
