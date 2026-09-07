document.getElementById("logout").addEventListener("click", (e) => {
  e.preventDefault();
  clearToken();
  window.location.href = "login.html";
});

async function renderApps() {
  try {
    const apps = await Api.listApps();
    document.getElementById("apps-table").innerHTML = apps
      .map(
        (app) => `
        <tr>
          <td style="font-weight:700; color:var(--text-heading);">${app.name}</td>
          <td><code>${app.app_key}</code></td>
          <td>${app.package_name}</td>
          <td><span style="text-transform:capitalize; font-weight:600;">${app.platform}</span></td>
          <td>${app.is_active ? '<span class="badge active"><span class="pulse-dot"></span> Active</span>' : '<span class="badge inactive">Inactive</span>'}</td>
          <td><button class="secondary" data-toggle="${app.id}" data-active="${app.is_active}">
            ${app.is_active ? "Deactivate" : "Activate"}
          </button></td>
        </tr>`
      )
      .join("");

    document.querySelectorAll("[data-toggle]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-toggle");
        const currentlyActive = btn.getAttribute("data-active") === "true";
        await Api.updateApp(id, { is_active: !currentlyActive });
        renderApps();
      });
    });
  } catch (err) {
    document.getElementById("apps-table").innerHTML =
      `<tr><td colspan="6" style="color:var(--badge-red-text);">Failed to load applications: ${err.message}</td></tr>`;
  }
}

document.getElementById("add-app-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("error");
  errorEl.style.display = "none";
  try {
    await Api.createApp({
      name: document.getElementById("name").value,
      app_key: document.getElementById("app_key").value,
      package_name: document.getElementById("package_name").value,
      platform: document.getElementById("platform").value,
      description: document.getElementById("description").value || null,
      is_active: true,
    });
    document.getElementById("add-app-form").reset();
    renderApps();
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.style.display = "block";
  }
});

renderApps();
