const rowsEl = document.getElementById("requestRows");
const searchInput = document.getElementById("searchInput");
const statusFilter = document.getElementById("statusFilter");
let reveal = new Set();
let timer;
const T = window.UI_TEXTS || {};

function esc(value) {
  return String(value ?? "").replace(/[&<>'"]/g, s => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;"}[s]));
}

function secretBlock(row, key, maskedKey, label) {
  const id = `${row.id}:${key}`;
  const shown = reveal.has(id);
  return `
    <span class="request-secret-item">
      <small>${esc(label)}</small>
      <b class="secret" data-id="${id}" data-full="${esc(row[key])}" data-mask="${esc(row[maskedKey])}">${shown ? esc(row[key]) : esc(row[maskedKey])}</b>
      <button class="request-secret-toggle" type="button" data-toggle-secret="${id}">${shown ? (T.hide || "Скрыть") : (T.show || "Показать")}</button>
    </span>
  `;
}

function statusPill(row) {
  return `<span class="status-pill status-${esc(row.status)}">${esc(T[row.status] || row.status_label)}</span>`;
}

function shortText(value, fallback = "-") {
  const text = String(value || "").trim();
  return esc(text || fallback);
}

function requestCard(row) {
  const title = row.full_name || row.company || `Заявка #${row.id}`;
  const subtitle = [row.company, row.department, row.position].filter(Boolean).join(" · ");
  return `
    <article class="request-card">
      <div class="request-card-main">
        <div class="request-id-badge">#${esc(row.id)}</div>
        <div class="request-card-body">
          <div class="request-card-title">
            <strong>${shortText(title)}</strong>
            ${statusPill(row)}
          </div>
          <p>${shortText(subtitle, "Предприятие не указано")}</p>
          <div class="request-chip-row">
            <span>${shortText(row.date)}</span>
            <span>${shortText(row.platform, "Платформа не указана")}</span>
            <span>${shortText(row.cause, "Причина не указана")}</span>
          </div>
        </div>
      </div>

      <div class="request-card-secrets">
        ${secretBlock(row, "pnfl", "pnfl_masked", "ПНФЛ")}
        ${secretBlock(row, "passport", "passport_masked", "Паспорт")}
        ${secretBlock(row, "phone", "phone_masked", "Телефон")}
        ${secretBlock(row, "telegram_id", "telegram_id_masked", "Telegram")}
      </div>

      <div class="request-card-actions">
        <a class="request-action primary" href="${esc(row.edit_url)}">${esc(T.editor || "Редактор")}</a>
        <a class="request-action" href="${esc(row.edit_url)}">${esc(T.block_unblock || "Блок/Разблок")}</a>
        <a class="request-action danger" href="${esc(row.edit_url)}">${esc(T.delete || "Удалить")}</a>
      </div>
    </article>
  `;
}

async function loadRows() {
  const url = new URL("/api/dashboard/requests/", window.location.origin);
  url.searchParams.set("q", searchInput.value || "");
  url.searchParams.set("status", statusFilter.value || "");
  const res = await fetch(url);
  const data = await res.json();
  rowsEl.innerHTML = data.rows.map(requestCard).join("") || `<div class="empty-state request-empty">${esc(T.no_requests || "Заявок не найдено")}</div>`;
}

document.addEventListener("click", event => {
  const btn = event.target.closest("[data-toggle-secret]");
  if (!btn) return;
  const id = btn.dataset.toggleSecret;
  if (reveal.has(id)) reveal.delete(id); else reveal.add(id);
  document.querySelectorAll(`[data-id="${CSS.escape(id)}"]`).forEach(el => el.textContent = reveal.has(id) ? el.dataset.full : el.dataset.mask);
  btn.textContent = reveal.has(id) ? (T.hide || "Скрыть") : (T.show || "Показать");
});

function scheduleLoad() {
  clearTimeout(timer);
  timer = setTimeout(loadRows, 220);
}

searchInput.addEventListener("input", scheduleLoad);
statusFilter.addEventListener("change", loadRows);
loadRows();
setInterval(loadRows, 15000);
