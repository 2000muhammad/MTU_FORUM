(() => {
  'use strict';

  const overlay = document.querySelector('.mtu-loader');
  if (!overlay) return;

  const root = document.documentElement;
  const percent = overlay.querySelector('[data-loader-percent]');
  const bar = overlay.querySelector('[data-loader-bar]');
  const label = overlay.querySelector('[data-loader-label]');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const startedAt = performance.now();
  const minimumVisibleMs = 1200;
  let progress = 0;
  let frame = 0;
  let timer = 0;
  let run = 0;

  const currentPath = window.location.pathname;
  const currentAuth = overlay.dataset.authenticated === 'true' ? '1' : '0';
  let previousPath = '';
  let previousAuth = '';
  let wasSeen = false;
  let forceNext = false;

  try {
    previousPath = sessionStorage.getItem('mtu-loader-path') || '';
    previousAuth = sessionStorage.getItem('mtu-loader-auth') || '';
    wasSeen = sessionStorage.getItem('mtu-loader-seen') === '1';
    forceNext = sessionStorage.getItem('mtu-loader-force-next') === '1';
    sessionStorage.removeItem('mtu-loader-force-next');
    sessionStorage.setItem('mtu-loader-path', currentPath);
    sessionStorage.setItem('mtu-loader-auth', currentAuth);
    sessionStorage.setItem('mtu-loader-seen', '1');
  } catch (_) {
    /* The first page still gets a loader when session storage is unavailable. */
  }

  const isLoginPage = /\/login\/$/.test(currentPath);
  const cameFromLoginPage = /\/login\/$/.test(previousPath);
  const authChanged = previousAuth !== '' && previousAuth !== currentAuth;
  const shouldShow = forceNext || !wasSeen || (isLoginPage && !cameFromLoginPage) || authChanged;

  const setProgress = (value) => {
    progress = Math.max(0, Math.min(100, value));
    percent.textContent = String(Math.round(progress)).padStart(3, '0');
    bar.style.setProperty('--loader-progress', `${progress}%`);
    label.textContent = progress < 28 ? overlay.dataset.initializing : progress < 68 ? overlay.dataset.assets : progress < 100 ? overlay.dataset.almostReady : overlay.dataset.welcome;
  };

  const animateProgress = (token) => {
    const began = performance.now();
    const tick = (now) => {
      if (token !== run || overlay.hidden) return;
      const elapsed = now - began;
      const value = 92 * (1 - Math.exp(-elapsed / 1800));
      setProgress(value);
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
  };

  const hide = () => {
    run += 1;
    cancelAnimationFrame(frame);
    clearTimeout(timer);
    overlay.classList.add('is-leaving');
    root.classList.remove('mtu-loader-active');
    timer = window.setTimeout(() => { overlay.hidden = true; }, reducedMotion.matches ? 0 : 720);
  };

  const finish = (token = run) => {
    if (token !== run) return;
    cancelAnimationFrame(frame);
    const initial = progress;
    const began = performance.now();
    const tick = (now) => {
      if (token !== run) return;
      const t = Math.min(1, (now - began) / 420);
      setProgress(initial + (100 - initial) * (1 - Math.pow(1 - t, 3)));
      if (t < 1) frame = requestAnimationFrame(tick);
      else timer = window.setTimeout(hide, reducedMotion.matches ? 0 : 260);
    };
    frame = requestAnimationFrame(tick);
  };

  const show = () => {
    run += 1;
    const token = run;
    cancelAnimationFrame(frame);
    clearTimeout(timer);
    overlay.hidden = false;
    overlay.classList.remove('is-leaving');
    root.classList.add('mtu-loader-active');
    setProgress(0);
    if (reducedMotion.matches || root.classList.contains('access-reduce-motion')) setProgress(90);
    else animateProgress(token);
    return token;
  };

  window.mtuLoader = { show, hide, finish, setProgress };

  document.addEventListener('click', (event) => {
    const link = event.target.closest('a.login-back-link');
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    try { sessionStorage.setItem('mtu-loader-force-next', '1'); } catch (_) {}
    show();
  });

  if (!shouldShow) {
    overlay.hidden = true;
    root.classList.remove('mtu-loader-active');
    return;
  }

  const token = show();
  const complete = () => {
    const remaining = Math.max(0, minimumVisibleMs - (performance.now() - startedAt));
    timer = window.setTimeout(() => finish(token), remaining);
  };

  if (document.readyState === 'complete') complete();
  else window.addEventListener('load', complete, { once: true });
  window.setTimeout(() => finish(token), 15000);

})();
