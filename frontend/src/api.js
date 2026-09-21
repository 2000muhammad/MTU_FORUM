function cookie(name) {
  return document.cookie.split(";").map(part => part.trim()).find(part => part.startsWith(`${name}=`))?.split("=").slice(1).join("=") || "";
}

export async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(options.method || "GET")) {
    headers.set("X-CSRFToken", decodeURIComponent(cookie("csrftoken")));
  }
  headers.set("Accept", "application/json");
  const response = await fetch(path, {...options, headers, credentials: "same-origin"});
  const type = response.headers.get("content-type") || "";
  const payload = type.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const error = new Error(response.status === 401 || response.status === 403 ? "Доступ запрещён или сессия завершена." : `Ошибка сервера (${response.status}).`);
    error.data = payload;
    throw error;
  }
  return payload;
}

export async function postLegacyForm(path, values) {
  const body = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    if (Array.isArray(value)) value.forEach(item => body.append(key, item));
    else if (value !== undefined && value !== null) body.append(key, value);
  });
  return api(path, {method: "POST", body, headers: {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"}});
}
