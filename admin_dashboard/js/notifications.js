document.getElementById("logout").addEventListener("click", (e) => {
  e.preventDefault();
  clearToken();
  window.location.href = "login.html";
});

let appsById = {};

async function loadApps() {
  const apps = await Api.listApps();
  appsById = Object.fromEntries(apps.map((a) => [a.id, a]));
  document.getElementById("application_id").innerHTML = apps
    .map((a) => `<option value="${a.id}">${a.name}</option>`)
    .join("");
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
  await loadHistory();
})();
