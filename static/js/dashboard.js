const rowsEl = document.getElementById("requestRows");
const searchInput = document.getElementById("searchInput");
const statusFilter = document.getElementById("statusFilter");
let reveal = new Set();
let timer;
const T = window.UI_TEXTS || {};

function esc(value) {
  return String(value ?? "").replace(/[&<>'"]/g, s => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;"}[s]));
}

function cellSecret(row, key, maskedKey) {
  const id = `${row.id}:${key}`;
  const shown = reveal.has(id);
  return `<span class="secret" data-id="${id}" data-full="${esc(row[key])}" data-mask="${esc(row[maskedKey])}">${shown ? esc(row[key]) : esc(row[maskedKey])}</span> <button class="mask-btn" data-toggle-secret="${id}">${shown ? (T.hide || 'Скрыть') : (T.show || 'Показать')}</button>`;
}

function statusPill(row) {
  return `<span class="status-pill status-${esc(row.status)}">${esc(T[row.status] || row.status_label)}</span>`;
}

async function loadRows() {
  const url = new URL('/api/dashboard/requests/', window.location.origin);
  url.searchParams.set('q', searchInput.value || '');
  url.searchParams.set('status', statusFilter.value || '');
  const res = await fetch(url);
  const data = await res.json();
  rowsEl.innerHTML = data.rows.map(row => `
    <tr>
      <td>#${esc(row.id)}</td><td>${esc(row.date)}</td><td>${esc(row.platform || '-')}</td><td>${esc(row.cause || '-')}</td>
      <td>${cellSecret(row,'pnfl','pnfl_masked')}</td><td>${esc(row.company || '-')}</td><td>${esc(row.department || '-')}</td><td>${esc(row.position || '-')}</td><td>${esc(row.full_name || '-')}</td>
      <td>${cellSecret(row,'passport','passport_masked')}</td><td>${cellSecret(row,'phone','phone_masked')}</td><td>${cellSecret(row,'telegram_id','telegram_id_masked')}</td>
      <td>${statusPill(row)}</td>
      <td><div class="dropdown"><button class="kebab" data-bs-toggle="dropdown">⋮</button><div class="dropdown-menu dropdown-menu-end"><a class="dropdown-item" href="${esc(row.edit_url)}">${esc(T.editor || 'Редактор')}</a><a class="dropdown-item" href="${esc(row.edit_url)}">${esc(T.block_unblock || 'Заблокировать/Разблокировать')}</a><a class="dropdown-item text-danger" href="${esc(row.edit_url)}">${esc(T.delete || 'Удалить')}</a></div></div></td>
    </tr>`).join('') || `<tr><td colspan="14" class="text-center text-secondary py-5">${esc(T.no_requests || 'Заявок не найдено')}</td></tr>`;
}

document.addEventListener('click', event => {
  const btn = event.target.closest('[data-toggle-secret]');
  if (!btn) return;
  const id = btn.dataset.toggleSecret;
  if (reveal.has(id)) reveal.delete(id); else reveal.add(id);
  document.querySelectorAll(`[data-id="${CSS.escape(id)}"]`).forEach(el => el.textContent = reveal.has(id) ? el.dataset.full : el.dataset.mask);
  btn.textContent = reveal.has(id) ? (T.hide || 'Скрыть') : (T.show || 'Показать');
});

function scheduleLoad() {
  clearTimeout(timer);
  timer = setTimeout(loadRows, 220);
}
searchInput.addEventListener('input', scheduleLoad);
statusFilter.addEventListener('change', loadRows);
loadRows();
setInterval(loadRows, 15000);
