"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { createTranslator } from "./i18n";

export function MtuLoader({ language = "ru" }) {
  const tr = useMemo(() => createTranslator(language), [language]);
  const overlayRef = useRef(null);
  const percentRef = useRef(null);
  const barRef = useRef(null);
  const labelRef = useRef(null);
  const [visible, setVisible] = useState(true);
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    const overlay = overlayRef.current;
    const percent = percentRef.current;
    const bar = barRef.current;
    const label = labelRef.current;
    if (!overlay || !percent || !bar || !label) return undefined;

    const root = document.documentElement;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const startedAt = performance.now();
    const currentPath = window.location.pathname;
    const currentAuth = /\/app\/(?:login|public)(?:\/|$)/.test(currentPath)
      ? "0"
      : "1";
    let previousPath = "";
    let previousAuth = "";
    let wasSeen = false;
    let forceNext = false;
    let progress = 0;
    let frame = 0;
    let timer = 0;
    let run = 1;

    try {
      previousPath = sessionStorage.getItem("mtu-loader-path") || "";
      previousAuth = sessionStorage.getItem("mtu-loader-auth") || "";
      wasSeen = sessionStorage.getItem("mtu-loader-seen") === "1";
      forceNext = sessionStorage.getItem("mtu-loader-force-next") === "1";
      sessionStorage.removeItem("mtu-loader-force-next");
      sessionStorage.setItem("mtu-loader-path", currentPath);
      sessionStorage.setItem("mtu-loader-auth", currentAuth);
      sessionStorage.setItem("mtu-loader-seen", "1");
    } catch {
      // The first load still shows the animation when session storage is unavailable.
    }

    const isLoginPage = /\/app\/login\/$/.test(currentPath);
    const cameFromLoginPage = /\/app\/login\/$/.test(previousPath);
    const cameFromLegacy =
      previousPath !== "" && !previousPath.startsWith("/app/");
    const authChanged = previousAuth !== "" && previousAuth !== currentAuth;
    const shouldShow =
      forceNext ||
      !wasSeen ||
      cameFromLegacy ||
      (isLoginPage && !cameFromLoginPage) ||
      authChanged;

    if (!shouldShow) {
      setVisible(false);
      root.classList.remove("mtu-loader-active");
      return undefined;
    }

    const labels = {
      initializing: tr("Подготовка"),
      assets: tr("Загрузка ресурсов"),
      almost: tr("Почти готово"),
      welcome: tr("Добро пожаловать"),
    };
    const setProgress = (value) => {
      progress = Math.max(0, Math.min(100, value));
      percent.textContent = String(Math.round(progress)).padStart(3, "0");
      bar.style.setProperty("--loader-progress", `${progress}%`);
      label.textContent =
        progress < 28
          ? labels.initializing
          : progress < 68
            ? labels.assets
            : progress < 100
              ? labels.almost
              : labels.welcome;
    };
    const hide = () => {
      run += 1;
      cancelAnimationFrame(frame);
      window.clearTimeout(timer);
      setLeaving(true);
      root.classList.remove("mtu-loader-active");
      timer = window.setTimeout(
        () => setVisible(false),
        reducedMotion.matches || root.classList.contains("access-reduce-motion")
          ? 0
          : 720,
      );
    };
    const finish = (token) => {
      if (token !== run) return;
      cancelAnimationFrame(frame);
      const initial = progress;
      const began = performance.now();
      const tick = (now) => {
        if (token !== run) return;
        const elapsed = Math.min(1, (now - began) / 420);
        setProgress(initial + (100 - initial) * (1 - Math.pow(1 - elapsed, 3)));
        if (elapsed < 1) frame = requestAnimationFrame(tick);
        else timer = window.setTimeout(hide, reducedMotion.matches ? 0 : 260);
      };
      frame = requestAnimationFrame(tick);
    };

    root.classList.add("mtu-loader-active");
    setProgress(0);
    const token = run;
    if (
      reducedMotion.matches ||
      root.classList.contains("access-reduce-motion")
    ) {
      setProgress(90);
    } else {
      const began = performance.now();
      const tick = (now) => {
        if (token !== run) return;
        setProgress(92 * (1 - Math.exp(-(now - began) / 1800)));
        frame = requestAnimationFrame(tick);
      };
      frame = requestAnimationFrame(tick);
    }

    const complete = () => {
      const remaining = Math.max(0, 1200 - (performance.now() - startedAt));
      timer = window.setTimeout(() => finish(token), remaining);
    };
    if (document.readyState === "complete") complete();
    else window.addEventListener("load", complete, { once: true });
    const fallback = window.setTimeout(() => finish(token), 15000);

    return () => {
      run += 1;
      cancelAnimationFrame(frame);
      window.clearTimeout(timer);
      window.clearTimeout(fallback);
      window.removeEventListener("load", complete);
      root.classList.remove("mtu-loader-active");
    };
  }, [language, tr]);

  return (
    <div
      ref={overlayRef}
      className={`mtu-loader ${leaving ? "is-leaving" : ""}`}
      hidden={!visible}
      role="status"
      aria-live="polite"
      aria-label={tr("Страница загружается")}
    >
      <div className="mtu-loader__stage">
        <div className="mtu-loader__orbit" aria-hidden="true">
          <i />
          <i />
          <i />
        </div>
        <div className="mtu-loader__content">
          <img
            className="mtu-loader__emblem"
            src="/static/img/mtu-loader-emblem.png"
            width="1084"
            height="1120"
            alt={tr("Филиал «Ташкентский региональный железнодорожный узел»")}
          />
          <div className="mtu-loader__kicker">
            <i aria-hidden="true" />
            <span>
              {tr("Филиал «Ташкентский региональный железнодорожный узел»")}
              <strong>{tr("Отдел цифровизации")}</strong>
            </span>
          </div>
          <div className="mtu-loader__logo" aria-hidden="true">
            <span>MTU FORUM</span>
          </div>
          <div className="mtu-loader__progress">
            <div className="mtu-loader__meta">
              <span ref={labelRef}>{tr("Подготовка")}</span>
              <strong>
                <span ref={percentRef}>000</span>
                <small>%</small>
              </strong>
            </div>
            <div className="mtu-loader__track">
              <span ref={barRef} />
            </div>
          </div>
        </div>
      </div>
      <div className="mtu-loader__corner" aria-hidden="true">
        <i />
        <i />
        <i />
      </div>
    </div>
  );
}
