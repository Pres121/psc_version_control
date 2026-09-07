// PSC Admin UI Utilities - Slide Menu & Global Interactions

document.addEventListener("DOMContentLoaded", () => {
  const menuToggle = document.getElementById("menu-toggle");
  const sidebar = document.getElementById("sidebar");
  const sidebarOverlay = document.getElementById("sidebar-overlay");
  const closeSidebarBtn = document.getElementById("close-sidebar");

  function openMenu() {
    if (sidebar) sidebar.classList.add("open");
    if (sidebarOverlay) sidebarOverlay.classList.add("open");
    document.body.style.overflow = "hidden";
  }

  function closeMenu() {
    if (sidebar) sidebar.classList.remove("open");
    if (sidebarOverlay) sidebarOverlay.classList.remove("open");
    document.body.style.overflow = "";
  }

  if (menuToggle) {
    menuToggle.addEventListener("click", (e) => {
      e.stopPropagation();
      if (sidebar && sidebar.classList.contains("open")) {
        closeMenu();
      } else {
        openMenu();
      }
    });
  }

  if (closeSidebarBtn) {
    closeSidebarBtn.addEventListener("click", closeMenu);
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener("click", closeMenu);
  }

  // Close sidebar on Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeMenu();
  });

  // Global logout handler
  const logoutBtn = document.getElementById("logout");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", (e) => {
      e.preventDefault();
      if (typeof clearToken === "function") {
        clearToken();
      } else {
        localStorage.removeItem("psc_admin_token");
      }
      window.location.href = "login.html";
    });
  }

  // Load User Info into Sidebar if authenticated
  if (typeof Api !== "undefined" && typeof getToken === "function" && getToken()) {
    Api.me()
      .then((user) => {
        const userNameEl = document.getElementById("sidebar-user-name");
        const userEmailEl = document.getElementById("sidebar-user-email");
        const userAvatarEl = document.getElementById("sidebar-user-avatar");

        if (userNameEl && user.full_name) userNameEl.textContent = user.full_name;
        if (userEmailEl && user.email) userEmailEl.textContent = user.email;
        if (userAvatarEl) {
          const initial = (user.full_name || user.email || "A").charAt(0).toUpperCase();
          userAvatarEl.textContent = initial;
        }
      })
      .catch(() => {
        // Ignored if not authenticated or error
      });
  }
});
