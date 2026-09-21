"use client";

import { useState } from "react";

export function VersionSwitch({ legacyUrl, oldLabel, newLabel, ariaLabel }) {
  const [switching, setSwitching] = useState(false);

  const openLegacy = (event) => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey)
      return;
    event.preventDefault();
    if (switching) return;
    setSwitching(true);
    try {
      window.sessionStorage.setItem("mtu-loader-force-next", "1");
    } catch {
      // Navigation still works if session storage is unavailable.
    }
    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    window.setTimeout(
      () => window.location.assign(legacyUrl),
      reduceMotion ? 0 : 260,
    );
  };

  return (
    <div
      className={`version-toggle is-new ${switching ? "is-switching-old" : ""}`}
      role="group"
      aria-label={ariaLabel}
      aria-busy={switching}
    >
      <span className="version-toggle-thumb" aria-hidden="true" />
      <a href={legacyUrl} onClick={openLegacy}>
        {oldLabel}
      </a>
      <span className="version-toggle-current" aria-current="page">
        {newLabel}
      </span>
    </div>
  );
}
