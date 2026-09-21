(() => {
  'use strict';
  const root = document.documentElement;
  const panel = document.querySelector('#solar-theme-panel');
  const manual = document.querySelector('[data-theme-toggle]');
  if (!panel || !manual) return;
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  const modes = ['auto', 'system', 'opposite'];
  let mode = readMode();
  function readMode() { try { const value = localStorage.getItem('mtu-theme-cycle'); return modes.includes(value) ? value : 'auto'; } catch { return 'auto'; } }
  const status = panel.querySelector('[data-solar-status]');
  const read = (key) => { try { return localStorage.getItem(key); } catch { return null; } };
  const save = (key, value) => { try { localStorage.setItem(key, value); } catch {} };
  let enabled = mode === 'auto';
  let generation = 0;
  let busy = false;
  let retryAt = 0;
  let schedule;
  try { schedule = JSON.parse(read('mtu-solar-schedule')); } catch {}
  const trigger = manual;
  const sunriseIcon = document.createElement('span');
  sunriseIcon.className = 'theme-icon theme-icon-sunrise';
  sunriseIcon.setAttribute('aria-hidden', 'true');
  sunriseIcon.innerHTML = '<svg class="mode-svg" viewBox="0 0 24 24"><path d="M3 17h18M4 21h16M7 17a5 5 0 0 1 10 0M12 2v7M9 5l3-3 3 3M3 10l2 2M19 12l2-2M2 14h2M20 14h2"/></svg>';
  trigger.append(sunriseIcon);
  trigger.removeAttribute('aria-controls');
  trigger.removeAttribute('aria-expanded');
  function sync() {
    trigger.classList.toggle('solar-auto-active', enabled);
    trigger.dataset.themeMode = mode;
    trigger.title = panel.dataset[mode];
    trigger.setAttribute('aria-label', panel.dataset[mode]);
  }
  function applySystem() {
    if (root.matches('.accessibility-mode, .access-black-white, .access-invert')) return;
    const dark = mode === 'opposite' ? !system.matches : system.matches;
    root.dataset.theme = dark ? 'dark' : 'light';
    save('mtu-theme', root.dataset.theme);
    trigger.classList.toggle('is-active', !dark);
    trigger.setAttribute('aria-pressed', String(!dark));
  }
  function dayAt(timeZone) {
    const parts = new Intl.DateTimeFormat('en', { timeZone, year:'numeric', month:'2-digit', day:'2-digit' }).formatToParts(new Date());
    const values = Object.fromEntries(parts.map(part => [part.type, part.value]));
    return `${values.year}-${values.month}-${values.day}`;
  }
  function valid(data) {
    if (!data || !data.tzid || !data.date) return false;
    try { return data.date === dayAt(data.tzid); } catch { return false; }
  }
  function apply() {
    if (!enabled || !valid(schedule)) return;
    const now = Date.now();
    let light;
    if (schedule.sun_status === 'midnight_sun') light = true;
    else if (schedule.sun_status === 'polar_night') light = false;
    else {
      const rise = Date.parse(schedule.sunrise), set = Date.parse(schedule.sunset);
      if (!Number.isFinite(rise) || !Number.isFinite(set)) return;
      light = rise <= set ? now >= rise && now < set : now >= rise || now < set;
    }
    // Accessibility contrast modes take priority over the automatic palette.
    if (!root.matches('.accessibility-mode, .access-black-white, .access-invert')) {
      const theme = light ? 'light' : 'dark';
      root.dataset.theme = theme;
      save('mtu-theme', theme);
      manual.classList.toggle('is-active', light);
      manual.setAttribute('aria-pressed', String(light));
      const label = manual.querySelector('[data-theme-label]');
      if (label) label.textContent = light ? label.dataset.night : label.dataset.day;
    }
    const format = value => value ? new Intl.DateTimeFormat(root.lang || 'en', {timeZone:schedule.tzid,hour:'2-digit',minute:'2-digit'}).format(new Date(value)) : '—';
    const details = `${panel.dataset.rise}: ${format(schedule.sunrise)} · ${panel.dataset.set}: ${format(schedule.sunset)} (${schedule.tzid})`;
    status.textContent = details;
    trigger.title = `${panel.dataset.auto} — ${details}`;
    trigger.setAttribute('aria-label', `${panel.dataset.auto}. ${details}`);
  }
  let preciseLocation;
  async function locate() {
    if (preciseLocation) return preciseLocation;
    if (read('mtu-location-enabled') === 'yes' && navigator.geolocation) {
      try {
        const permission = navigator.permissions ? await navigator.permissions.query({name:'geolocation'}) : null;
        if (permission?.state === 'granted') {
          return await new Promise((resolve,reject) => navigator.geolocation.getCurrentPosition(position => resolve({lat:Number(position.coords.latitude.toFixed(2)),lng:Number(position.coords.longitude.toFixed(2))}), reject, {enableHighAccuracy:false,timeout:8000,maximumAge:300000}));
        }
      } catch {}
    }
    const providers = [
      {url:'https://ipwho.is/', parse:data => data.success === false ? null : {lat:data.latitude,lng:data.longitude}},
      {url:'https://ipapi.co/json/', parse:data => data.error ? null : {lat:data.latitude,lng:data.longitude}},
    ];
    for (const provider of providers) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 7000);
      try {
        const response = await fetch(provider.url, {signal:controller.signal, credentials:'omit', referrerPolicy:'no-referrer'});
        if (!response.ok) continue;
        const location = provider.parse(await response.json());
        if (location && Number.isFinite(Number(location.lat)) && Number.isFinite(Number(location.lng))) {
          return {lat:Number(Number(location.lat).toFixed(2)),lng:Number(Number(location.lng).toFixed(2))};
        }
      } catch {} finally { clearTimeout(timer); }
    }
    // MTU FORUM is primarily used in Uzbekistan. This keeps automatic mode
    // useful if both privacy-friendly IP lookups are unavailable.
    const browserZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (browserZone === 'Asia/Tashkent') return {lat:41.31,lng:69.24};
    throw new Error('Location unavailable');
  }
  async function update(force = false) {
    if (!enabled || busy) return;
    if (!force && valid(schedule)) { apply(); return; }
    if (!force && Date.now() < retryAt) return;
    busy = true;
    const token = generation;
    status.textContent = panel.dataset.loading;
    try {
      const location = await locate();
      if (token !== generation || !enabled) return;
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 10000);
      let data;
      try {
        const params = new URLSearchParams({...location, date:'today', time_format:'iso8601'});
        const response = await fetch(`https://api.sunrise-sunset.org/v2?${params}`, {signal:controller.signal, credentials:'omit', referrerPolicy:'no-referrer'});
        if (!response.ok) throw new Error('Sun times unavailable');
        data = await response.json();
      } finally { clearTimeout(timeout); }
      if (token !== generation || !enabled) return;
      if (data.error || !valid(data) || (data.sun_status !== 'midnight_sun' && data.sun_status !== 'polar_night' && (!Number.isFinite(Date.parse(data.sunrise)) || !Number.isFinite(Date.parse(data.sunset))))) throw new Error('Incomplete sun times');
      // Store only the daily schedule, never the user's coordinates.
      schedule = {date:data.date,tzid:data.tzid,sunrise:data.sunrise,sunset:data.sunset,sun_status:data.sun_status};
      save('mtu-solar-schedule', JSON.stringify(schedule));
      retryAt = 0;
      apply();
    } catch {
      if (token === generation && enabled) {
        retryAt = Date.now() + 15 * 60 * 1000;
        status.textContent = panel.dataset.error;
        if (!valid(schedule)) applySystem();
        trigger.title = panel.dataset.auto + ' — ' + panel.dataset.fallback;
      }
    } finally { busy = false; }
  }
  window.addEventListener('mtu-location-ready', event => {
    preciseLocation = event.detail;
    schedule = null;
    save('mtu-solar-schedule', 'null');
    retryAt = 0;
    generation++;
    // An earlier IP lookup may still be finishing; retry on the next tick.
    if (!busy) update(true);
    else setTimeout(() => update(true), 1000);
  });
  trigger.addEventListener('click', event => {
    event.stopImmediatePropagation();
    event.preventDefault();
    generation++;
    mode = modes[(modes.indexOf(mode) + 1) % modes.length];
    enabled = mode === 'auto';
    save('mtu-theme-cycle', mode);
    sync();
    if (enabled) { applySystem(); update(); } else applySystem();
  }, {capture:true});
  system.addEventListener('change', () => { if (!enabled || !valid(schedule)) applySystem(); });
  window.addEventListener('storage', event => {
    if (event.key === 'mtu-theme-cycle') {
      generation++; mode = readMode(); enabled = mode === 'auto'; sync();
      if (enabled) update(); else applySystem();
    }
  });
  document.addEventListener('visibilitychange', () => { if (!document.hidden) update(); });
  setInterval(() => update(), 30000);
  sync();
  if (enabled && valid(schedule)) apply(); else applySystem();
  update();
})();
