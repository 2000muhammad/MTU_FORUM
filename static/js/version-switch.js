(() => {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  document.addEventListener("click", (event) => {
    const link = event.target.closest("[data-version-target]");
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

    const control = link.closest("[data-version-switch]");
    if (!control) return;

    event.preventDefault();
    try { sessionStorage.setItem("mtu-loader-force-next", "1"); } catch (_) {}
    control.classList.remove("is-switching-old", "is-switching-new");
    control.classList.add(`is-switching-${link.dataset.versionTarget}`);
    control.setAttribute("aria-busy", "true");

    window.setTimeout(() => window.location.assign(link.href), reduceMotion.matches ? 0 : 260);
  });
})();
