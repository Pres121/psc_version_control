document.getElementById("logout").addEventListener("click", (e) => {
  e.preventDefault();
  clearToken();
  window.location.href = "login.html";
});

let appsById = {};

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function loadApps() {
  const apps = await Api.listApps();
  appsById = Object.fromEntries(apps.map((a) => [a.id, a]));
  const options = apps.map((a) => `<option value="${a.id}">${escapeHtml(a.name)}</option>`).join("");
  document.getElementById("application_id").innerHTML = options;
  document.getElementById("announcement_application_id").innerHTML = options;
  await loadReleasesForSelectedApp();
}

async function loadReleasesForSelectedApp() {
  const appId = document.getElementById("application_id").value;
  if (!appId) return;
  const releases = await Api.listReleases({ application_id: appId });
  const published = releases.filter((r) => r.is_published);
  const selectEl = document.getElementById("release_id");
  if (published.length === 0) {
    selectEl.innerHTML = `<option value="">No published releases available</option>`;
  } else {
    selectEl.innerHTML = published
      .map((r) => `<option value="${r.id}">${r.platform.toUpperCase()} v${r.version} (Build ${r.build_number})</option>`)
      .join("");
  }
}

document.getElementById("application_id").addEventListener("change", loadReleasesForSelectedApp);

async function loadAnnouncements() {
  try {
    const rows = await Api.listAnnouncements();
    const tbody = document.getElementById("announcements-table");
    if (!rows.length) {
      tbody.innerHTML =
        `<tr><td colspan="4" style="text-align:center; padding: 24px; color: var(--text-muted);">No in-app announcements yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = rows
      .map((row) => {
        const appName = appsById[row.application_id]?.name || row.application_id;
        const message = String(row.message || "");
        const shortMessage = message.length > 80 ? `${message.slice(0, 80)}…` : message;
        return `
          <tr>
            <td style="font-weight:700; color:var(--text-heading);">${escapeHtml(appName)}</td>
            <td>${escapeHtml(row.title)}</td>
            <td>${escapeHtml(shortMessage)}</td>
            <td>${row.created_at ? new Date(row.created_at).toLocaleString() : "—"}</td>
          </tr>`;
      })
      .join("");
  } catch (err) {
    document.getElementById("announcements-table").innerHTML =
      `<tr><td colspan="4" style="color:var(--badge-red-text);">Failed to load: ${escapeHtml(err.message)}</td></tr>`;
  }
}

async function loadHistory() {
  try {
    const history = await Api.notificationHistory();
    document.getElementById("history-table").innerHTML = history
      .map((h) => {
        const appName = appsById[h.application_id]?.name || h.application_id;
        const badgeClass = h.status === "sent" ? "sent" : h.status === "failed" ? "failed" : "draft";
        return `
          <tr>
            <td style="font-weight:700; color:var(--text-heading);">${appName}</td>
            <td>${h.title}</td>
            <td><code>${h.fcm_topic}</code></td>
            <td><span class="badge ${badgeClass}"><span class="pulse-dot"></span> ${h.status}</span></td>
            <td>${h.targeted_device_count != null ? h.targeted_device_count : "—"}</td>
            <td>${h.sent_at ? new Date(h.sent_at).toLocaleString() : "—"}</td>
          </tr>`;
      })
      .join("");
  } catch (err) {
    document.getElementById("history-table").innerHTML =
      `<tr><td colspan="6" style="color:var(--badge-red-text);">Failed to load history: ${err.message}</td></tr>`;
  }
}

document.getElementById("announcement-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("announcement-error");
  errorEl.style.display = "none";
  try {
    await Api.createAnnouncement({
      application_id: document.getElementById("announcement_application_id").value,
      title: document.getElementById("announcement_title").value,
      message: document.getElementById("announcement_message").value,
    });
    document.getElementById("announcement-form").reset();
    await loadApps();
    await loadAnnouncements();
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.style.display = "block";
  }
});

document.getElementById("notify-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("error");
  errorEl.style.display = "none";

  const releaseId = document.getElementById("release_id").value;
  if (!releaseId) {
    errorEl.textContent = "Please select a valid published release before sending notification.";
    errorEl.style.display = "block";
    return;
  }

  try {
    await Api.sendNotification({
      application_id: document.getElementById("application_id").value,
      release_id: releaseId,
      title: document.getElementById("title").value,
      message: document.getElementById("message").value,
    });
    document.getElementById("notify-form").reset();
    await loadHistory();
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.style.display = "block";
  }
});

(async () => {
  await loadApps();
  await loadAnnouncements();
  await loadHistory();
})();
