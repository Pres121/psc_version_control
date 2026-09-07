document.getElementById("logout").addEventListener("click", (e) => {
  e.preventDefault();
  clearToken();
  window.location.href = "login.html";
});

function latestPublished(releases, platform) {
  const pub = releases.filter((r) => r.platform === platform && r.is_published);
  if (pub.length === 0) return null;
  return pub.sort((a, b) => versionCompare(b.version, a.version))[0];
}

function versionCompare(a, b) {
  const pa = a.split(".").map(Number);
  const pb = b.split(".").map(Number);
  for (let i = 0; i < 3; i++) {
    if ((pa[i] || 0) !== (pb[i] || 0)) return (pa[i] || 0) - (pb[i] || 0);
  }
  return 0;
}

async function load() {
  try {
    const apps = await Api.listApps();
    const rows = [];
    let updatesAvailable = 0;
    let mandatoryCount = 0;
    let totalReleases = 0;
    const recent = [];

    for (const app of apps) {
      const releases = await Api.appReleaseHistory(app.id);
      totalReleases += releases.length;
      const androidLatest = latestPublished(releases, "android");
      const iosLatest = latestPublished(releases, "ios");
      if (androidLatest || iosLatest) updatesAvailable++;
      if (releases.some((r) => r.is_mandatory && r.is_published)) mandatoryCount++;

      releases
        .slice()
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .slice(0, 1)
        .forEach((r) => recent.push({ app: app.name, ...r }));

      rows.push(`
        <tr>
          <td style="font-weight:700; color:var(--text-heading);">${app.name}</td>
          <td><code>${androidLatest ? androidLatest.version : "—"}</code></td>
          <td><code>${iosLatest ? iosLatest.version : "—"}</code></td>
          <td>${
            app.is_active
              ? '<span class="badge active"><span class="pulse-dot"></span> Active</span>'
              : '<span class="badge inactive">Inactive</span>'
          }</td>
        </tr>
      `);
    }

    document.getElementById("apps-table").innerHTML = rows.join("");

    document.getElementById("stats").innerHTML = `
      <div class="stat-card">
        <div class="stat-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/></svg>
        </div>
        <div class="stat-info">
          <div class="stat-value">${apps.length}</div>
          <div class="stat-label">Total Applications</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
        </div>
        <div class="stat-info">
          <div class="stat-value">${totalReleases}</div>
          <div class="stat-label">Total Releases</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>
        </div>
        <div class="stat-info">
          <div class="stat-value">${updatesAvailable}</div>
          <div class="stat-label">Published Updates</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        </div>
        <div class="stat-info">
          <div class="stat-value">${mandatoryCount}</div>
          <div class="stat-label">Mandatory Updates</div>
        </div>
      </div>
    `;
  } catch (err) {
    document.getElementById("apps-table").innerHTML =
      `<tr><td colspan="4" style="color:var(--badge-red-text);">Failed to load: ${err.message}</td></tr>`;
  }
}

load();
