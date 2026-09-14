// PSC Admin UI Utilities - Slide Menu & Global Interactions

document.addEventListener("DOMContentLoaded", () => {
  const menuToggle = document.getElementById("menu-toggle");
  const sidebar = document.getElementById("sidebar");
  const sidebarOverlay = document.getElementById("sidebar-overlay");
  const closeSidebarBtn = document.getElementById("close-sidebar");
  const appWrapper = document.querySelector(".app-wrapper");
  const SIDEBAR_KEY = "psc_sidebar_collapsed";

  function isDesktop() {
    return window.matchMedia("(min-width: 1024px)").matches;
  }

  function openMobileMenu() {
    if (sidebar) sidebar.classList.add("open");
    if (sidebarOverlay) sidebarOverlay.classList.add("open");
    document.body.style.overflow = "hidden";
  }

  function closeMobileMenu() {
    if (sidebar) sidebar.classList.remove("open");
    if (sidebarOverlay) sidebarOverlay.classList.remove("open");
    document.body.style.overflow = "";
  }

  function setDesktopCollapsed(collapsed) {
    if (!sidebar || !appWrapper) return;
    sidebar.classList.toggle("closed", collapsed);
    appWrapper.classList.toggle("full-width", collapsed);
    localStorage.setItem(SIDEBAR_KEY, collapsed ? "1" : "0");
    if (menuToggle) {
      menuToggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
      menuToggle.setAttribute(
        "aria-label",
        collapsed ? "Expand navigation" : "Collapse navigation"
      );
    }
  }

  function toggleSidebar() {
    if (isDesktop()) {
      const collapsed = !sidebar.classList.contains("closed");
      setDesktopCollapsed(collapsed);
    } else if (sidebar.classList.contains("open")) {
      closeMobileMenu();
    } else {
      openMobileMenu();
    }
  }

  // Restore desktop preference
  if (isDesktop() && localStorage.getItem(SIDEBAR_KEY) === "1") {
    setDesktopCollapsed(true);
  } else if (isDesktop()) {
    setDesktopCollapsed(false);
  }

  if (menuToggle) {
    menuToggle.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleSidebar();
    });
  }

  if (closeSidebarBtn) {
    closeSidebarBtn.addEventListener("click", closeMobileMenu);
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener("click", closeMobileMenu);
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeMobileMenu();
  });

  window.addEventListener("resize", () => {
    if (isDesktop()) {
      closeMobileMenu();
      setDesktopCollapsed(localStorage.getItem(SIDEBAR_KEY) === "1");
    } else {
      sidebar?.classList.remove("closed");
      appWrapper?.classList.remove("full-width");
    }
  });

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
      .catch(() => {});
  }
});
