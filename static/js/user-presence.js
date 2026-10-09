(() => {
  const csrfToken = () => document.cookie.split('; ').find((item) => item.startsWith('csrftoken='))?.split('=').slice(1).join('=') || '';
  const heartbeat = () => {
    if (document.visibilityState !== 'visible') return;
    fetch('/api/presence/heartbeat/', {method:'POST', headers:{'X-CSRFToken':decodeURIComponent(csrfToken()), Accept:'application/json'}, credentials:'same-origin'}).catch(() => {});
  };
  const updatePresence = async () => {
    const cards = [...document.querySelectorAll('[data-user-presence-id]')];
    if (!cards.length) return;
    try {
      const response = await fetch('/api/presence/state/', {headers:{Accept:'application/json'}, credentials:'same-origin'});
      if (!response.ok) return;
      const data = await response.json();
      const states = new Map((data.users || []).map((item) => [String(item.id), Boolean(item.online)]));
      cards.forEach((card) => {
        const online = states.get(card.dataset.userPresenceId) === true;
        const badge = card.querySelector('[data-presence-label]');
        if (!badge) return;
        badge.textContent = online ? 'Онлайн' : 'Офлайн';
        badge.classList.toggle('is-online', online);
        badge.classList.toggle('is-offline', !online);
      });
    } catch (_) {}
  };
  document.querySelectorAll('[data-excel-import]').forEach((form) => {
    const input = form.querySelector('input[type=file]');
    form.querySelector('[data-excel-import-button]')?.addEventListener('click', () => input?.click());
    input?.addEventListener('change', () => { if (input.files.length) form.submit(); });
  });
  const selectAll = document.querySelector('[data-select-all-users]');
  const userChecks = [...document.querySelectorAll('[data-user-select]')];
  selectAll?.addEventListener('change', () => userChecks.forEach((item) => { item.checked = selectAll.checked; }));
  document.querySelector('[data-bulk-users-form]')?.addEventListener('submit', (event) => {
    if (!userChecks.some((item) => item.checked)) { event.preventDefault(); window.alert('Выберите хотя бы одного пользователя.'); return; }
    if (event.submitter?.matches('[data-bulk-delete]') && !window.confirm('Удалить выбранных пользователей?')) event.preventDefault();
  });
  const importJobs = [...document.querySelectorAll('[data-import-job-id]')];
  const pollImportJobs = async () => {
    await Promise.all(importJobs.map(async (item) => {
      try {
        const response = await fetch(`/api/people-import/${item.dataset.importJobId}/`, {headers:{Accept:'application/json'}});
        if (!response.ok) return;
        const data = await response.json();
        item.querySelector('[data-import-job-status]').textContent = {preview:'Предпросмотр',queued:'В очереди',running:'Выполняется',completed:'Завершён',failed:'Ошибка'}[data.status] || data.status;
        const progress = item.querySelector('progress'); if (progress) { progress.max = data.total || 1; progress.value = data.processed || 0; }
      } catch (_) {}
    }));
  };
  if (importJobs.length) { pollImportJobs(); window.setInterval(pollImportJobs, 3000); }
  heartbeat(); updatePresence();
  window.setInterval(heartbeat, 20000);
  window.setInterval(updatePresence, 15000);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') { heartbeat(); updatePresence(); } });
})();
