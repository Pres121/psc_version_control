document.getElementById("logout").addEventListener("click", (e) => {
  e.preventDefault();
  clearToken();
  window.location.href = "login.html";
});

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function ensureSuperadmin() {
  const me = await Api.me();
  if (me.role !== "superadmin") {
    document.querySelector("main").innerHTML =
      `<div class="card"><h3>Access denied</h3><p>Only superadmins can manage admin users.</p></div>`;
    throw new Error("not superadmin");
  }
}

async function loadAdmins() {
  const rows = await Api.listAdmins();
  const tbody = document.getElementById("admins-table");
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:24px;">No admins yet.</td></tr>`;
    return;
  }
  tbody.innerHTML = rows
    .map((row) => {
      const status = row.is_active
        ? `<span class="badge active">Active</span>`
        : `<span class="badge inactive">Inactive</span>`;
      const toggleLabel = row.is_active ? "Deactivate" : "Activate";
      return `
        <tr>
          <td style="font-weight:700;color:var(--text-heading);">${escapeHtml(row.full_name || "—")}</td>
          <td>${escapeHtml(row.email)}</td>
          <td><code>${escapeHtml(row.role)}</code></td>
          <td>${status}</td>
          <td>
            <button class="secondary action-button" data-toggle="${row.id}" data-active="${row.is_active}">
              ${toggleLabel}
            </button>
          </td>
        </tr>`;
    })
    .join("");

  tbody.querySelectorAll("[data-toggle]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        const next = btn.getAttribute("data-active") !== "true";
        await Api.updateAdmin(btn.getAttribute("data-toggle"), { is_active: next });
        await loadAdmins();
      } catch (err) {
        alert(err.message);
      }
    });
  });
}

document.getElementById("admin-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("error");
  const successEl = document.getElementById("success");
  errorEl.style.display = "none";
  successEl.style.display = "none";

  const payload = {
    email: document.getElementById("email").value.trim(),
    full_name: document.getElementById("full_name").value.trim() || null,
    role: document.getElementById("role").value,
  };
  const password = document.getElementById("password").value.trim();
  if (password) payload.password = password;

  try {
    const result = await Api.createAdmin(payload);
    let msg = `Created ${result.admin.email}.`;
    if (result.email_sent) {
      msg += " Invite email sent.";
    } else if (result.temporary_password) {
      msg += ` Share this temporary password securely: ${result.temporary_password}`;
    }
    successEl.textContent = msg;
    successEl.style.display = "block";
    document.getElementById("admin-form").reset();
    await loadAdmins();
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.style.display = "block";
  }
});

(async () => {
  try {
    await ensureSuperadmin();
    await loadAdmins();
  } catch (_) {
    // Access denied UI already rendered, or redirected by api.js
  }
})();
