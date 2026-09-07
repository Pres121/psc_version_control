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
}

async function loadReleases() {
  try {
    const releases = await Api.listReleases();
    document.getElementById("releases-table").innerHTML = releases
      .map((r) => {
        const appName = appsById[r.application_id]?.name || r.application_id;
        const statusBadge = r.is_published
          ? '<span class="badge published"><span class="pulse-dot"></span> Published</span>'
          : '<span class="badge draft">Draft</span>';
        const mandatoryBadge = r.is_mandatory
          ? '<span class="badge mandatory">Mandatory</span>'
          : '<span style="color:var(--text-muted);">Optional</span>';
        return `
          <tr>
            <td style="font-weight:700; color:var(--text-heading);">${appName}</td>
            <td><span style="text-transform:capitalize; font-weight:600;">${r.platform}</span></td>
            <td><code>${r.version}</code></td>
            <td><code>${r.build_number}</code></td>
            <td>${statusBadge}</td>
            <td>${mandatoryBadge}</td>
            <td>${
              r.is_published
                ? '<span style="color:var(--text-muted); font-size:12px;">—</span>'
                : `<button class="primary" style="padding: 6px 12px; font-size: 12px;" data-publish="${r.id}" data-app="${appName}" data-version="${r.version}">Publish</button>`
            }</td>
          </tr>`;
      })
      .join("");

    document.querySelectorAll("[data-publish]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const app = btn.getAttribute("data-app");
        const version = btn.getAttribute("data-version");
        const confirmed = confirm(
          `Publish ${app} ${version}? This makes it visible to all client apps immediately.`
        );
        if (!confirmed) return;
        await Api.publishRelease(btn.getAttribute("data-publish"));
        loadReleases();
      });
    });
  } catch (err) {
    document.getElementById("releases-table").innerHTML =
      `<tr><td colspan="7" style="color:var(--badge-red-text);">Failed to load releases: ${err.message}</td></tr>`;
  }
}

document.getElementById("release-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("error");
  errorEl.style.display = "none";

  const notes = document
    .getElementById("release_notes")
    .value.split("\n")
    .map((s) => s.trim())
    .filter(Boolean);

  try {
    await Api.createRelease({
      application_id: document.getElementById("application_id").value,
      platform: document.getElementById("platform").value,
      version: document.getElementById("version").value,
      build_number: parseInt(document.getElementById("build_number").value, 10),
      release_title: document.getElementById("release_title").value || null,
      release_notes: notes,
      minimum_supported_version: document.getElementById("minimum_supported_version").value,
      is_mandatory: document.getElementById("is_mandatory").checked,
      update_url: document.getElementById("update_url").value,
      is_published: false,
    });
    document.getElementById("release-form").reset();
    loadReleases();
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.style.display = "block";
  }
});

(async () => {
  await loadApps();
  await loadReleases();
})();
