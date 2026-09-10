document.getElementById("logout").addEventListener("click", (e) => {
  e.preventDefault();
  clearToken();
  window.location.href = "login.html";
});

let appsByKey = {};

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function resultBadge(result) {
  if (!result) return `<span class="badge draft">—</span>`;
  if (result === "update_available" || result === "update_required" || result === "registered") {
    return `<span class="badge sent">${escapeHtml(result)}</span>`;
  }
  if (String(result).startsWith("error") || result === "unknown_app_key") {
    return `<span class="badge failed">${escapeHtml(result)}</span>`;
  }
  return `<span class="badge draft">${escapeHtml(result)}</span>`;
}

function eventLabel(eventType) {
  if (eventType === "update_check") return "Update check";
  if (eventType === "device_register") return "Device register";
  return eventType || "—";
}

async function loadApps() {
  const apps = await Api.listApps();
  appsByKey = Object.fromEntries(apps.map((a) => [a.app_key, a]));
  const select = document.getElementById("filter-app");
  select.innerHTML =
    `<option value="">All apps</option>` +
    apps.map((a) => `<option value="${escapeHtml(a.app_key)}">${escapeHtml(a.name)}</option>`).join("");
}

function currentFilters() {
  const params = {};
  const eventType = document.getElementById("filter-event").value;
  const appKey = document.getElementById("filter-app").value;
  const ip = document.getElementById("filter-ip").value.trim();
  const limit = document.getElementById("filter-limit").value;
  if (eventType) params.event_type = eventType;
  if (appKey) params.app_key = appKey;
  if (ip) params.ip_address = ip;
  if (limit) params.limit = limit;
  return params;
}

async function loadLogs() {
  const tbody = document.getElementById("logs-table");
  try {
    const logs = await Api.listLogs(currentFilters());
    if (!logs.length) {
      tbody.innerHTML =
        `<tr><td colspan="7" style="text-align:center; padding: 24px; color: var(--text-muted);">No matching logs yet. Open a PSC app to generate an update-check entry.</td></tr>`;
      return;
    }

    tbody.innerHTML = logs
      .map((log) => {
        const appName = appsByKey[log.app_key]?.name || log.app_key || "—";
        const version =
          log.app_version != null
            ? `${escapeHtml(log.app_version)}${log.build_number != null ? ` (${escapeHtml(log.build_number)})` : ""}`
            : "—";
        return `
          <tr>
            <td>${log.created_at ? new Date(log.created_at).toLocaleString() : "—"}</td>
            <td>${escapeHtml(eventLabel(log.event_type))}</td>
            <td style="font-weight:700; color:var(--text-heading);">${escapeHtml(appName)}</td>
            <td>${log.platform ? escapeHtml(String(log.platform).toUpperCase()) : "—"}</td>
            <td>${version}</td>
            <td><code>${escapeHtml(log.ip_address || "—")}</code></td>
            <td>${resultBadge(log.result)}</td>
          </tr>`;
      })
      .join("");
  } catch (err) {
    tbody.innerHTML =
      `<tr><td colspan="7" style="color:var(--badge-red-text);">Failed to load logs: ${escapeHtml(err.message)}</td></tr>`;
  }
}

document.getElementById("logs-filters").addEventListener("submit", async (e) => {
  e.preventDefault();
  await loadLogs();
});

document.getElementById("refresh-logs").addEventListener("click", async () => {
  await loadLogs();
});

(async () => {
  await loadApps();
  await loadLogs();
})();
