const rowsEl = document.getElementById("requestRows");
const searchInput = document.getElementById("searchInput");
const statusFilter = document.getElementById("statusFilter");
let reveal = new Set();
const revealedValues = new Map();
let timer;
const T = window.UI_TEXTS || {};
const confirmModal = document.getElementById("secretConfirmModal");
const confirmForm = document.getElementById("secretConfirmForm");
const confirmPassword = document.getElementById("secretConfirmPassword");
const confirmError = document.getElementById("secretConfirmError");
let pendingSecret = null;

function esc(value) {
  return String(value ?? "").replace(/[&<>'"]/g, s => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;"}[s]));
}

function secretBlock(row, key, maskedKey, label) {
  const id = `${row.id}:${key}`;
  const shown = reveal.has(id);
  const visibleValue = revealedValues.get(id) || "";
  return `
    <span class="request-secret-item">
      <small>${esc(label)}</small>
      <b class="secret" data-id="${id}" data-mask="${esc(row[maskedKey])}">${shown ? esc(visibleValue) : esc(row[maskedKey])}</b>
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
        <a class="request-action primary" href="${esc(row.edit_url)}">${esc(T.open_editor || "Открыть редактор")}</a>
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

function closeSecretConfirm() {
  if (!confirmModal) return;
  confirmModal.hidden = true;
  confirmPassword.value = "";
  confirmError.textContent = "";
  pendingSecret = null;
  document.documentElement.classList.remove("modal-open");
}

document.addEventListener("click", event => {
  const btn = event.target.closest("[data-toggle-secret]");
  if (!btn) return;
  const id = btn.dataset.toggleSecret;
  if (reveal.has(id)) {
    reveal.delete(id);
    revealedValues.delete(id);
    document.querySelectorAll(`[data-id="${CSS.escape(id)}"]`).forEach(el => { el.textContent = el.dataset.mask; });
    btn.textContent = T.show || "Показать";
    return;
  }
  const [requestId, field] = id.split(":");
  pendingSecret = { id, requestId, field, button: btn };
  confirmModal.hidden = false;
  document.documentElement.classList.add("modal-open");
  window.setTimeout(() => confirmPassword.focus(), 30);
});

confirmForm?.addEventListener("submit", async event => {
  event.preventDefault();
  if (!pendingSecret) return;
  const submit = confirmForm.querySelector('[type="submit"]');
  submit.disabled = true;
  confirmError.textContent = "";
  try {
    const response = await fetch("/api/dashboard/requests/reveal/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": confirmForm.querySelector('[name="csrfmiddlewaretoken"]').value,
      },
      body: JSON.stringify({
        request_id: pendingSecret.requestId,
        field: pendingSecret.field,
        password: confirmPassword.value,
      }),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || "Не удалось подтвердить пароль.");
    const { id, button } = pendingSecret;
    reveal.add(id);
    revealedValues.set(id, data.value);
    document.querySelectorAll(`[data-id="${CSS.escape(id)}"]`).forEach(el => { el.textContent = data.value; });
    button.textContent = T.hide || "Скрыть";
    closeSecretConfirm();
  } catch (error) {
    confirmError.textContent = error.message;
    confirmPassword.select();
  } finally {
    submit.disabled = false;
  }
});

document.querySelectorAll("[data-secret-cancel]").forEach(button => button.addEventListener("click", closeSecretConfirm));
document.addEventListener("keydown", event => {
  if (event.key === "Escape" && confirmModal && !confirmModal.hidden) closeSecretConfirm();
});

function scheduleLoad() {
  clearTimeout(timer);
  timer = setTimeout(loadRows, 220);
}

searchInput.addEventListener("input", scheduleLoad);
statusFilter.addEventListener("change", loadRows);
loadRows();
setInterval(loadRows, 15000);
