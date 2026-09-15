document.getElementById("logout").addEventListener("click", (e) => {
  e.preventDefault();
  clearToken();
  window.location.href = "login.html";
});

let appsById = {};
let releaseRecords = [];
let pendingReleaseAction = null;

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
    releaseRecords = releases;
    refreshReleaseGuidance();
    document.getElementById("releases-table").innerHTML = releases
      .map((r) => {
        const appName = appsById[r.application_id]?.name || r.application_id;
        const statusBadge = r.is_published
          ? '<span class="badge published"><span class="pulse-dot"></span> Published</span>'
          : '<span class="badge draft">Draft</span>';
        const mandatoryBadge = r.is_mandatory
          ? '<span class="badge mandatory">Mandatory</span>'
          : '<span style="color:var(--text-muted);">Optional</span>';
        const binaryBadge = r.storage_path
          ? `<span class="badge sent" title="${escapeAttr(r.file_name || r.storage_path)}">Uploaded</span>`
          : '<span class="badge draft">No file</span>';
        return `
          <tr>
            <td style="font-weight:700; color:var(--text-heading);">${appName}</td>
            <td><span style="text-transform:capitalize; font-weight:600;">${r.platform}</span></td>
            <td><code>${r.version}</code></td>
            <td><code>${r.build_number}</code></td>
            <td>${binaryBadge}</td>
            <td>${statusBadge}</td>
            <td>${mandatoryBadge}</td>
            <td><div class="release-actions">
              <button class="secondary action-button" data-release-action="edit" data-release-id="${r.id}">Edit</button>
              <label class="secondary action-button" style="cursor:pointer; margin:0;">
                Upload
                <input type="file" accept=".apk,.aab,.ipa,.zip" data-upload-release-id="${r.id}" hidden />
              </label>
              <button class="${r.is_published ? "secondary" : "primary"} action-button" data-release-action="${r.is_published ? "unpublish" : "publish"}" data-release-id="${r.id}">${r.is_published ? "Unpublish" : "Publish"}</button>
              <button class="danger action-button" data-release-action="delete" data-release-id="${r.id}">Delete</button>
            </div></td>
          </tr>`;
      })
      .join("");

    document.querySelectorAll("[data-release-action]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const release = releaseRecords.find((item) => item.id === btn.dataset.releaseId);
        if (release) openReleaseAction(btn.dataset.releaseAction, release);
      });
    });

    document.querySelectorAll("[data-upload-release-id]").forEach((input) => {
      input.addEventListener("change", async () => {
        const file = input.files && input.files[0];
        if (!file) return;
        try {
          showUploadProgress(0, `Starting ${file.name}…`);
          await Api.uploadReleaseBinary(input.dataset.uploadReleaseId, file, (percent, label) => {
            showUploadProgress(percent, label || `Uploading ${file.name}…`);
          });
          hideUploadProgress();
          await loadReleases();
          showReleaseMessage("success", `Uploaded ${file.name}. It replaces the previous build for this app/platform.`);
        } catch (err) {
          hideUploadProgress();
          showReleaseMessage("error", err.message);
        } finally {
          input.value = "";
        }
      });
    });
  } catch (err) {
    document.getElementById("releases-table").innerHTML =
      `<tr><td colspan="8" style="color:var(--badge-red-text);">Failed to load releases: ${err.message}</td></tr>`;
  }
}

function escapeAttr(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;");
}

document.getElementById("release-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("error");
  const successEl = document.getElementById("success");
  errorEl.style.display = "none";
  successEl.style.display = "none";

  const notes = document
    .getElementById("release_notes")
    .value.split("\n")
    .map((s) => s.trim())
    .filter(Boolean);

  const validationError = validateReleaseSequence();
  if (validationError) {
    showReleaseMessage("error", validationError);
    return;
  }

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
      update_url: document.getElementById("update_url").value.trim() || null,
      is_published: false,
    });
    document.getElementById("release-form").reset();
    loadReleases();
    showReleaseMessage("success", "Draft release created. Review it in Release History, then publish when ready.");
  } catch (err) {
    showReleaseMessage("error", err.message);
  }
});

function releasesForSelectedTarget() {
  const applicationId = document.getElementById("application_id").value;
  const platform = document.getElementById("platform").value;
  return releaseRecords.filter(
    (release) => release.application_id === applicationId && release.platform === platform
  );
}

function compareVersions(left, right) {
  const parse = (version) => {
    const [core, prerelease = ""] = version.split("-", 2);
    return { core: core.split(".").map(Number), prerelease };
  };
  const a = parse(left);
  const b = parse(right);
  for (let index = 0; index < 3; index++) {
    if ((a.core[index] || 0) !== (b.core[index] || 0)) {
      return (a.core[index] || 0) - (b.core[index] || 0);
    }
  }
  if (a.prerelease === b.prerelease) return 0;
  if (!a.prerelease) return 1;
  if (!b.prerelease) return -1;
  return a.prerelease.localeCompare(b.prerelease);
}

function latestReleaseForTarget() {
  const releases = releasesForSelectedTarget();
  if (!releases.length) return null;
  return releases.reduce((latest, release) =>
    compareVersions(release.version, latest.version) > 0 ? release : latest
  );
}

function refreshReleaseGuidance() {
  const latest = latestReleaseForTarget();
  const versionHint = document.getElementById("version-guidance");
  const buildHint = document.getElementById("build-guidance");
  const buildInput = document.getElementById("build_number");

  if (!latest) {
    versionHint.textContent = "No releases yet for this application and platform. Start at 1.0.0.";
    buildHint.textContent = "Start with build number 1.";
    buildInput.min = "1";
    return;
  }

  const highestBuild = Math.max(...releasesForSelectedTarget().map((release) => release.build_number));
  versionHint.textContent = `Latest version: ${latest.version}. Enter a higher version.`;
  buildHint.textContent = `Latest build: ${highestBuild}. Use build ${highestBuild + 1} or higher.`;
  buildInput.min = String(highestBuild + 1);
}

function validateReleaseSequence() {
  const version = document.getElementById("version").value.trim();
  const build = Number(document.getElementById("build_number").value);
  const releases = releasesForSelectedTarget();
  if (!releases.length) return null;

  if (releases.some((release) => release.version === version)) {
    return `Version ${version} already exists for this application and platform.`;
  }

  const latest = latestReleaseForTarget();
  if (compareVersions(version, latest.version) < 0) {
    return `Version ${version} is lower than the existing version ${latest.version}.`;
  }

  const highestBuild = Math.max(...releases.map((release) => release.build_number));
  if (build <= highestBuild) {
    return `Build number ${build} must be higher than the existing build ${highestBuild}.`;
  }
  return null;
}

function showReleaseMessage(type, message) {
  const element = document.getElementById(type === "success" ? "success" : "error");
  const other = document.getElementById(type === "success" ? "error" : "success");
  other.style.display = "none";
  element.textContent = message;
  element.style.display = "block";
}

function showUploadProgress(percent, label) {
  const wrap = document.getElementById("upload-progress");
  const bar = document.getElementById("upload-progress-bar");
  const labelEl = document.getElementById("upload-progress-label");
  const percentEl = document.getElementById("upload-progress-percent");
  if (!wrap || !bar || !labelEl || !percentEl) return;
  const safe = Math.max(0, Math.min(100, Math.round(Number(percent) || 0)));
  wrap.hidden = false;
  bar.style.width = `${safe}%`;
  labelEl.textContent = label || "Uploading…";
  percentEl.textContent = `${safe}%`;
  document.getElementById("success").style.display = "none";
  document.getElementById("error").style.display = "none";
}

function hideUploadProgress() {
  const wrap = document.getElementById("upload-progress");
  if (wrap) wrap.hidden = true;
}

function openReleaseAction(action, release) {
  pendingReleaseAction = { action, release };
  const app = appsById[release.application_id];
  const dialog = document.getElementById("release-action-dialog");
  const editFields = document.getElementById("edit-release-fields");
  const labels = {
    edit: ["Edit release", "Verify this release before changing its details or version.", "Save changes"],
    publish: ["Publish release", "Publishing makes this release available to client apps immediately.", "Publish release"],
    unpublish: ["Unpublish release", "This removes the release from future update checks.", "Unpublish release"],
    delete: ["Delete release", "This permanently removes the release and cannot be undone.", "Delete release"],
  };
  const [title, description, submitLabel] = labels[action];
  document.getElementById("action-dialog-title").textContent = title;
  document.getElementById("action-dialog-description").textContent = description;
  document.getElementById("action-submit").textContent = submitLabel;
  document.getElementById("verify_app_key").value = "";
  document.getElementById("action-error").style.display = "none";

  const isEdit = action === "edit";
  editFields.hidden = !isEdit;

  // Prefill from the existing release; required attrs only apply while editing
  // so publish/unpublish/delete are not blocked by empty edit inputs.
  ["edit_version", "edit_build_number", "edit_minimum_supported_version"].forEach((id) => {
    document.getElementById(id).required = isEdit;
  });

  document.getElementById("edit_version").value = release.version || "";
  document.getElementById("edit_build_number").value = release.build_number ?? "";
  document.getElementById("edit_release_title").value = release.release_title || "";
  document.getElementById("edit_release_notes").value = (release.release_notes || []).join("\n");
  document.getElementById("edit_minimum_supported_version").value =
    release.minimum_supported_version || "";
  document.getElementById("edit_update_url").value = release.update_url || "";
  document.getElementById("edit_is_mandatory").checked = Boolean(release.is_mandatory);
  const editUpload = document.getElementById("edit_upload_file");
  if (editUpload) editUpload.value = "";

  if (app?.app_key) {
    document.getElementById("verify_app_key").placeholder = app.app_key;
  }

  dialog.showModal();
}

function closeReleaseAction() {
  document.getElementById("release-action-dialog").close();
  pendingReleaseAction = null;
}

document.querySelectorAll("[data-close-dialog]").forEach((button) => {
  button.addEventListener("click", closeReleaseAction);
});

document.getElementById("release-action-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!pendingReleaseAction) return;
  const { action, release } = pendingReleaseAction;
  const app = appsById[release.application_id];
  const verification = {
    app_key: document.getElementById("verify_app_key").value.trim(),
  };
  const errorElement = document.getElementById("action-error");
  errorElement.style.display = "none";

  if (verification.app_key !== app?.app_key) {
    errorElement.textContent = "App key does not match. Re-enter it exactly to confirm.";
    errorElement.style.display = "block";
    return;
  }

  const submitButton = document.getElementById("action-submit");
  submitButton.disabled = true;
  try {
    if (action === "edit") {
      const notes = document.getElementById("edit_release_notes").value.split("\n").map((note) => note.trim()).filter(Boolean);
      await Api.updateRelease(release.id, {
        ...verification,
        version: document.getElementById("edit_version").value.trim(),
        build_number: Number(document.getElementById("edit_build_number").value),
        release_title: document.getElementById("edit_release_title").value.trim() || null,
        release_notes: notes,
        minimum_supported_version: document.getElementById("edit_minimum_supported_version").value.trim(),
        update_url: document.getElementById("edit_update_url").value.trim() || null,
        is_mandatory: document.getElementById("edit_is_mandatory").checked,
      });
      const uploadInput = document.getElementById("edit_upload_file");
      if (uploadInput?.files?.[0]) {
        const file = uploadInput.files[0];
        showUploadProgress(0, `Starting ${file.name}…`);
        await Api.uploadReleaseBinary(release.id, file, (percent, label) => {
          showUploadProgress(percent, label || `Uploading ${file.name}…`);
        });
        hideUploadProgress();
        uploadInput.value = "";
      }
    } else if (action === "publish") {
      await Api.publishRelease(release.id, verification);
    } else if (action === "unpublish") {
      await Api.unpublishRelease(release.id, verification);
    } else {
      await Api.deleteRelease(release.id, verification);
    }
    closeReleaseAction();
    await loadReleases();
    showReleaseMessage("success", `Release ${action === "edit" ? "updated" : action === "delete" ? "deleted" : `${action}ed`} successfully.`);
  } catch (err) {
    hideUploadProgress();
    errorElement.textContent = err.message;
    errorElement.style.display = "block";
  } finally {
    submitButton.disabled = false;
  }
});

(async () => {
  await loadApps();
  await loadReleases();
})();

["application_id", "platform"].forEach((id) => {
  document.getElementById(id).addEventListener("change", refreshReleaseGuidance);
});
