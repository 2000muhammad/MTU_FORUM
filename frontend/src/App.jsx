import { useCallback, useEffect, useMemo, useState } from "react";
import {
  NavLink,
  Navigate,
  Route,
  Routes,
  useLocation,
  useParams,
} from "react-router-dom";
import {
  BarChart3,
  Building2,
  CheckCircle2,
  ClipboardList,
  Code2,
  ExternalLink,
  Languages,
  ListTodo,
  LogOut,
  Menu,
  MessageCircle,
  MessagesSquare,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  PlugZap,
  ScrollText,
  Search,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Sun,
  Sunrise,
  UserCircle,
  UserCog,
  Users,
  XCircle,
} from "lucide-react";
import { api, postLegacyForm } from "./api";
import { createTranslator } from "./i18n";
import { useSolarTheme } from "./useSolarTheme";
import { VersionSwitch } from "./VersionSwitch";
import { AccessibilityControl } from "./AccessibilityControl";

const statusLabels = {
  new: "Новая",
  done: "Сделано",
  blocked: "Заблокирована",
};
const moduleMeta = {
  messages: {
    title: "Сообщения",
    subtitle: "Внутренние диалоги",
    icon: MessagesSquare,
  },
  chats: {
    title: "Чаты",
    subtitle: "Обращения пользователей",
    icon: MessageCircle,
  },
  tasks: { title: "Задания", subtitle: "Работа с заданиями", icon: ListTodo },
  users: {
    title: "Пользователи",
    subtitle: "Управление сотрудниками",
    icon: Users,
  },
  managers: {
    title: "Менеджеры",
    subtitle: "Управление менеджерами",
    icon: UserCog,
  },
  settings: {
    title: "Все справочники",
    subtitle: "Настройки системных данных",
    icon: Settings2,
  },
  api_settings: {
    title: "API настройки",
    subtitle: "Интеграции и подключения",
    icon: PlugZap,
  },
  site_settings: {
    title: "Настройки сайта",
    subtitle: "Параметры платформы",
    icon: SlidersHorizontal,
  },
  logs: { title: "Логи сайта", subtitle: "Журнал событий", icon: ScrollText },
  programmers: {
    title: "Разработчики",
    subtitle: "Команда проекта",
    icon: Code2,
  },
  profile: { title: "Профиль", subtitle: "Личные настройки", icon: UserCircle },
};

function useRemote(loader, dependencies = []) {
  const [state, setState] = useState({ loading: true, data: null, error: "" });
  const load = useCallback(async () => {
    setState((current) => ({ ...current, loading: true, error: "" }));
    try {
      setState({ loading: false, data: await loader(), error: "" });
    } catch (error) {
      setState({ loading: false, data: null, error: error.message });
    }
  }, dependencies); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    load();
  }, [load]);
  return { ...state, reload: load };
}

function Loading({ tr = createTranslator("ru") }) {
  return (
    <div className="state-card">
      <span className="spinner" />
      {tr("Загрузка…")}
    </div>
  );
}
function ErrorState({ message, retry, tr = createTranslator("ru") }) {
  return (
    <div className="state-card error">
      <XCircle />
      <div>
        <strong>{tr("Не удалось загрузить данные")}</strong>
        <p>{message}</p>
      </div>
      <button onClick={retry}>{tr("Повторить")}</button>
    </div>
  );
}

function Layout({ boot, config, children }) {
  const tr = createTranslator(boot.language);
  const [open, setOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(
    () =>
      typeof window !== "undefined" &&
      window.localStorage.getItem("mtu-sidebar-collapsed") === "on",
  );
  const {
    mode: themeMode,
    theme,
    cycle: cycleTheme,
    loading: solarLoading,
    details: solarDetails,
  } = useSolarTheme(boot.language);
  const [accessOpen, setAccessOpen] = useState(false);
  const [languageOpen, setLanguageOpen] = useState(false);
  const location = useLocation();
  const routeCategory =
    location.pathname.startsWith("/requests") ||
    location.pathname.startsWith("/modules/tasks")
      ? "work"
      : /^\/modules\/(messages|chats)/.test(location.pathname)
        ? "communication"
        : /^\/modules\/(users|managers)/.test(location.pathname)
          ? "people"
          : location.pathname.startsWith("/directories") ||
              location.pathname.startsWith("/modules/")
            ? "system"
            : "work";
  const [navCategory, setNavCategory] = useState(routeCategory);
  const moduleKey = location.pathname.split("/")[2];
  const currentTitle = tr(
    moduleMeta[moduleKey]?.title ||
      (/^\/requests\/\d+\/edit\/?$/.test(location.pathname)
        ? "Редактор заявки"
        : /^\/requests\/?$/.test(location.pathname)
          ? "Заявки"
          : location.pathname.includes("positions")
            ? "Должности"
            : location.pathname.includes("stations")
              ? "Предприятия"
              : boot.page_title || "MTU FORUM"),
  );
  const isModuleWorkspace =
    location.pathname.startsWith("/modules/") ||
    /^\/requests\/\d+\/edit/.test(location.pathname);
  useEffect(() => {
    setOpen(false);
  }, [location.pathname]);
  useEffect(() => {
    setNavCategory(routeCategory);
  }, [routeCategory]);
  useEffect(() => {
    document.documentElement.lang = boot.language || "ru";
  }, [boot.language]);
  useEffect(() => {
    window.localStorage.setItem(
      "mtu-sidebar-collapsed",
      sidebarCollapsed ? "on" : "off",
    );
  }, [sidebarCollapsed]);
  const legacy = boot.legacy_links;
  const renderModuleLinks = (keys) =>
    keys
      .filter((key) => legacy[key])
      .map((key) => {
        const Icon = moduleMeta[key].icon;
        return (
          <NavLink key={key} to={`/modules/${key}`}>
            <Icon />
            {tr(moduleMeta[key].title)}
          </NavLink>
        );
      });
  const categoryMeta = {
    work: { label: tr("Работа"), icon: BarChart3 },
    communication: { label: tr("Общение"), icon: MessagesSquare },
    people: { label: tr("Управление"), icon: Users },
    system: { label: tr("Система"), icon: Settings2 },
  };
  const languageHref = (code) =>
    `/${code}/app${location.pathname === "/" ? "/" : `${location.pathname}/`}`.replace(
      /\/+/g,
      "/",
    );
  const themeTitle =
    themeMode === "auto"
      ? `${tr("Авто: восход и закат")}${solarDetails ? ` — ${solarDetails}` : solarLoading ? ` — ${tr("Получение времени…")}` : ""}`
      : themeMode === "system"
        ? tr("Как в системе")
        : tr("Противоположно системе");
  return (
    <div className="app-layout">
      <aside
        className={`side side-v3 ${open ? "open" : ""} ${sidebarCollapsed ? "collapsed" : ""}`}
      >
        <div className="side-head">
          <NavLink to="/" className="brand" title={boot.site.name}>
            <img src="/static/img/mtu-forum-mark.svg" alt="" />
            <span>{boot.site.name}</span>
          </NavLink>
          <button
            type="button"
            className="sidebar-collapse-button"
            onClick={() => setSidebarCollapsed((current) => !current)}
            aria-label={tr(
              sidebarCollapsed ? "Развернуть меню" : "Свернуть меню",
            )}
            title={tr(sidebarCollapsed ? "Развернуть меню" : "Свернуть меню")}
            aria-pressed={sidebarCollapsed}
          >
            {sidebarCollapsed ? <PanelLeftOpen /> : <PanelLeftClose />}
          </button>
        </div>
        <div className="side-navigation">
          <nav className="category-rail" aria-label={tr("Навигация")}>
            {Object.entries(categoryMeta).map(([key, item]) => {
              const Icon = item.icon;
              return (
                <button
                  key={key}
                  type="button"
                  className={navCategory === key ? "active" : ""}
                  onClick={() => setNavCategory(key)}
                  aria-label={item.label}
                  title={item.label}
                  aria-pressed={navCategory === key}
                >
                  <Icon />
                </button>
              );
            })}
          </nav>
          <div className="category-panel">
            <div className="category-heading">
              <small>{tr("Навигация")}</small>
              <strong>{categoryMeta[navCategory].label}</strong>
            </div>
            <nav aria-label={categoryMeta[navCategory].label}>
              {navCategory === "work" && (
                <>
                  {boot.permissions.dashboard && (
                    <NavLink end to="/">
                      <BarChart3 />
                      {tr("Dashboard")}
                    </NavLink>
                  )}
                  {boot.permissions.requests && (
                    <NavLink to="/requests">
                      <ClipboardList />
                      {tr("Заявки")}
                    </NavLink>
                  )}
                  {renderModuleLinks(["tasks"])}
                </>
              )}
              {navCategory === "communication" &&
                renderModuleLinks(["messages", "chats"])}
              {navCategory === "people" &&
                renderModuleLinks(["users", "managers"])}
              {navCategory === "system" && (
                <>
                  {boot.permissions.directories && (
                    <NavLink to="/directories/stations">
                      <Building2 />
                      {tr("Предприятия / должности")}
                    </NavLink>
                  )}
                  {renderModuleLinks([
                    "settings",
                    "api_settings",
                    "site_settings",
                    "logs",
                    "programmers",
                    "profile",
                  ])}
                </>
              )}
            </nav>
          </div>
        </div>
        <div className="side-user">
          <span>{boot.user.initial}</span>
          <div>
            <strong>{boot.user.username}</strong>
            <small>{tr(boot.user.role)}</small>
          </div>
        </div>
        <a className="logout" href={legacy.logout}>
          <LogOut />
          {tr("Выйти")}
        </a>
      </aside>
      <div className="workspace">
        <header>
          <button
            className="mobile-menu"
            onClick={() => setOpen(!open)}
            aria-label={tr(open ? "Закрыть меню" : "Открыть меню")}
          >
            <Menu />
          </button>
          <div>
            <small>{tr("КОРПОРАТИВНАЯ ЖЕЛЕЗНОДОРОЖНАЯ ПЛАТФОРМА")}</small>
            <h1>{currentTitle}</h1>
          </div>
          <div className="new-tools">
            <VersionSwitch
              legacyUrl={boot.version_links.old}
              oldLabel={tr("Старая версия")}
              newLabel={tr("Новая версия")}
              ariaLabel={tr("Версия платформы")}
            />
            <button
              className={`icon-button solar-react-button ${themeMode === "auto" ? "active" : ""}`}
              data-theme-mode={themeMode}
              onClick={cycleTheme}
              aria-label={themeTitle}
              title={themeTitle}
            >
              {themeMode === "auto" ? (
                <Sunrise />
              ) : theme === "light" ? (
                <Sun />
              ) : (
                <Moon />
              )}
            </button>
            <AccessibilityControl
              language={boot.language}
              open={accessOpen}
              onOpenChange={(nextOpen) => {
                setAccessOpen(nextOpen);
                if (nextOpen) setLanguageOpen(false);
              }}
            />
            <div className="tool-menu">
              <button
                className={`icon-button language-button ${languageOpen ? "active" : ""}`}
                onClick={() => {
                  setLanguageOpen(!languageOpen);
                  setAccessOpen(false);
                }}
                aria-label={tr("Выбрать язык")}
                title={tr("Выбрать язык")}
              >
                <Languages />
                <span>
                  {(boot.language || "ru")
                    .toUpperCase()
                    .replace("UZ-CYRL", "ЎЗ")}
                </span>
              </button>
              {languageOpen && (
                <nav
                  className="react-popover language-popover"
                  aria-label={tr("Выбрать язык")}
                >
                  <a href={languageHref("ru")}>
                    RU <span>Русский</span>
                  </a>
                  <a href={languageHref("uz")}>
                    UZ <span>O‘zbekcha</span>
                  </a>
                  <a href={languageHref("uz-cyrl")}>
                    ЎЗ <span>Ўзбекча</span>
                  </a>
                  <a href={languageHref("en")}>
                    EN <span>English</span>
                  </a>
                </nav>
              )}
            </div>
          </div>
        </header>
        <main className={isModuleWorkspace ? "module-main" : ""}>
          {children}
        </main>
      </div>
      {open && (
        <button
          className="scrim"
          onClick={() => setOpen(false)}
          aria-label={tr("Закрыть меню")}
        />
      )}
    </div>
  );
}

function Dashboard({ boot }) {
  const tr = createTranslator(boot.language);
  const stats = boot.dashboard.stats;
  return (
    <div className="page-stack">
      <section className="hero">
        <div>
          <span>{tr("ОБЗОР СИСТЕМЫ")}</span>
          <h2>
            {tr("Добро пожаловать, {name}", {
              name: boot.user.first_name || boot.user.username,
            })}
          </h2>
          <p>
            {tr(
              "Актуальное состояние заявок и быстрый доступ к рабочим сервисам.",
            )}
          </p>
        </div>
        <ShieldCheck />
      </section>
      {boot.permissions.requests && (
        <section className="metric-grid">
          <article>
            <span>{tr("Новые заявки")}</span>
            <strong>{stats.new}</strong>
            <ClipboardList />
          </article>
          <article>
            <span>{tr("Выполнено")}</span>
            <strong>{stats.done}</strong>
            <CheckCircle2 />
          </article>
          <article>
            <span>{tr("Заблокировано")}</span>
            <strong>{stats.blocked}</strong>
            <XCircle />
          </article>
          <article>
            <span>{tr("Непрочитанные чаты")}</span>
            <strong>{stats.chats}</strong>
            <Users />
          </article>
        </section>
      )}
      <section className="panel">
        <div className="panel-head">
          <div>
            <span>{tr("ПО ПЛАТФОРМАМ")}</span>
            <h2>{tr("Статистика заявок")}</h2>
          </div>
        </div>
        <div className="platform-grid">
          {boot.dashboard.platforms.map((item) => (
            <article className="platform-card" key={item.name}>
              <h3>{item.name}</h3>
              <div>
                <span>
                  {tr("Всего")} <b>{item.total}</b>
                </span>
                <span>
                  {tr("Готово")} <b>{item.done}</b>
                </span>
                <span>
                  {tr("Блок")} <b>{item.blocked}</b>
                </span>
                <span>
                  {tr("Удалено")} <b>{item.deleted}</b>
                </span>
              </div>
            </article>
          ))}
          {!boot.dashboard.platforms.length && (
            <p className="muted">{tr("Нет доступных платформ.")}</p>
          )}
        </div>
      </section>
      <section className="panel">
        <div className="panel-head">
          <div>
            <span>{tr("БЫСТРЫЙ ДОСТУП")}</span>
            <h2>{tr("WEB-платформы")}</h2>
          </div>
        </div>
        <div className="service-grid">
          {boot.dashboard.web_platforms.map((item) => (
            <a
              href={item.open_url}
              target="_blank"
              rel="noreferrer"
              key={item.id}
            >
              <div>{item.image_url ? <img src={item.image_url} /> : "WEB"}</div>
              <strong>{item.name}</strong>
              <small>
                {item.uses} {tr("открытий")}
              </small>
            </a>
          ))}
        </div>
      </section>
    </div>
  );
}

function RequestsPage({ language }) {
  const tr = createTranslator(language);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [revealed, setRevealed] = useState(new Set());
  const endpoint = `/api/dashboard/requests/?q=${encodeURIComponent(query)}&status=${encodeURIComponent(status)}`;
  const { loading, data, error, reload } = useRemote(
    () => api(endpoint),
    [endpoint],
  );
  const toggle = (key) =>
    setRevealed((current) => {
      const next = new Set(current);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  return (
    <div className="page-stack">
      <section className="panel">
        <div className="panel-head">
          <div>
            <span>{tr("РАБОЧАЯ ОЧЕРЕДЬ")}</span>
            <h2>{tr("Заявки")}</h2>
          </div>
          <b>{data?.count ?? 0}</b>
        </div>
        <div className="filters">
          <label>
            <Search />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={tr("Поиск по ФИО, ПНФЛ, предприятию…")}
            />
          </label>
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">{tr("Все статусы")}</option>
            <option value="new">{tr("Новые")}</option>
            <option value="done">{tr("Сделано")}</option>
            <option value="blocked">{tr("Заблокированные")}</option>
          </select>
        </div>
      </section>
      {loading ? (
        <Loading tr={tr} />
      ) : error ? (
        <ErrorState message={error} retry={reload} tr={tr} />
      ) : (
        <section className="request-list">
          {data.rows.map((row) => (
            <article key={row.id}>
              <div className="request-main">
                <span className="request-number">#{row.id}</span>
                <div>
                  <div className="request-title">
                    <strong>
                      {row.full_name ||
                        row.company ||
                        `${tr("Заявки")} #${row.id}`}
                    </strong>
                    <span className={`pill ${row.status}`}>
                      {tr(statusLabels[row.status])}
                    </span>
                  </div>
                  <p>
                    {[row.company, row.department, row.position]
                      .filter(Boolean)
                      .join(" · ") || tr("Предприятие не указано")}
                  </p>
                  <div className="chips">
                    <span>{row.date}</span>
                    <span>{row.platform || tr("Без платформы")}</span>
                    <span>{row.cause || tr("Без причины")}</span>
                  </div>
                </div>
              </div>
              <div className="secrets">
                {[
                  ["pnfl", "ПНФЛ"],
                  ["passport", "Паспорт"],
                  ["phone", "Телефон"],
                  ["telegram_id", "Telegram"],
                ].map(([key, label]) => {
                  const id = `${row.id}:${key}`;
                  return (
                    <div key={key}>
                      <small>{tr(label)}</small>
                      <b>
                        {revealed.has(id) ? row[key] : row[`${key}_masked`]}
                      </b>
                      <button onClick={() => toggle(id)}>
                        {tr(revealed.has(id) ? "Скрыть" : "Показать")}
                      </button>
                    </div>
                  );
                })}
              </div>
              <NavLink
                className="primary-button"
                to={`/requests/${row.id}/edit`}
              >
                {tr("Открыть редактор")}
              </NavLink>
            </article>
          ))}
          {!data.rows.length && (
            <div className="state-card">{tr("Заявок не найдено.")}</div>
          )}
        </section>
      )}
    </div>
  );
}

function DirectoryPage({ kind, boot }) {
  const tr = createTranslator(boot.language);
  const title = kind === "stations" ? "Предприятия" : "Должности";
  const section = kind === "stations" ? "station" : "position";
  const { loading, data, error, reload } = useRemote(
    () => api(`/api/react/directories/${kind}/`),
    [kind],
  );
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(new Set());
  const [editing, setEditing] = useState(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  useEffect(() => {
    setSelected(new Set());
    setEditing(null);
    setNotice("");
  }, [kind]);
  const rows = useMemo(
    () =>
      (data?.rows || []).filter((row) =>
        `${row.name} ${row.code || ""} ${row.branch_name || ""} ${row.organization_name || ""}`
          .toLowerCase()
          .includes(query.toLowerCase()),
      ),
    [data, query],
  );
  const submit = async (values) => {
    setBusy(true);
    setNotice("");
    try {
      await postLegacyForm(data.post_url, values);
      setEditing(null);
      setSelected(new Set());
      await reload();
      setNotice(tr("Изменения сохранены."));
    } catch (e) {
      setNotice(e.message);
    } finally {
      setBusy(false);
    }
  };
  const bulk = (action) =>
    submit({ section: `${section}_bulk`, action, selected_ids: [...selected] });
  return (
    <div className="page-stack">
      <div className="directory-tabs">
        <NavLink to="/directories/stations">{tr("Предприятия")}</NavLink>
        <NavLink to="/directories/positions">{tr("Должности")}</NavLink>
        <NavLink to="/modules/settings">
          {tr("Остальные справочники")} <ExternalLink />
        </NavLink>
      </div>
      <section className="panel">
        <div className="panel-head">
          <div>
            <span>{tr("СПРАВОЧНИК")}</span>
            <h2>{tr(title)}</h2>
          </div>
          <button
            className="primary-button"
            onClick={() =>
              setEditing({
                id: "",
                name: "",
                branch_id: "",
                organization_id: "",
                sort_order: 0,
                is_active: true,
              })
            }
          >
            {tr("Добавить")}
          </button>
        </div>
        <div className="filters">
          <label>
            <Search />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={tr("Поиск…")}
            />
          </label>
        </div>
        {notice && <p className="notice">{notice}</p>}
      </section>
      {selected.size > 0 && (
        <div className="bulk-bar">
          <b>{tr("Выбрано: {count}", { count: selected.size })}</b>
          <button onClick={() => bulk("bulk_activate")} disabled={busy}>
            {tr("Включить")}
          </button>
          <button onClick={() => bulk("bulk_deactivate")} disabled={busy}>
            {tr("Отключить")}
          </button>
        </div>
      )}
      {loading ? (
        <Loading tr={tr} />
      ) : error ? (
        <ErrorState message={error} retry={reload} tr={tr} />
      ) : (
        <section className="directory-list">
          <label className="select-all">
            <input
              type="checkbox"
              checked={rows.length > 0 && selected.size === rows.length}
              onChange={(e) =>
                setSelected(
                  e.target.checked
                    ? new Set(rows.map((r) => String(r.id)))
                    : new Set(),
                )
              }
            />{" "}
            {tr("Выбрать все")}
          </label>
          {rows.map((row) => (
            <article key={row.id}>
              <input
                type="checkbox"
                checked={selected.has(String(row.id))}
                onChange={(e) =>
                  setSelected((current) => {
                    const next = new Set(current);
                    e.target.checked
                      ? next.add(String(row.id))
                      : next.delete(String(row.id));
                    return next;
                  })
                }
              />
              <div>
                <strong>{row.name}</strong>
                <small>
                  {row.code ||
                    tr(kind === "positions" ? "Должность" : "Без кода")}
                </small>
              </div>
              <div>
                <span>{row.branch_name || tr("Без филиала")}</span>
                <small>{row.organization_name || tr("Без организации")}</small>
              </div>
              <span className={`pill ${row.is_active ? "done" : "blocked"}`}>
                {tr(row.is_active ? "Активно" : "Отключено")}
              </span>
              <button onClick={() => setEditing(row)}>
                {tr("Редактировать")}
              </button>
            </article>
          ))}
          {!rows.length && (
            <div className="state-card">{tr("Записей не найдено.")}</div>
          )}
        </section>
      )}
      {editing && (
        <div
          className="modal-backdrop"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) setEditing(null);
          }}
        >
          <form
            className="modal"
            onSubmit={(e) => {
              e.preventDefault();
              const form = new FormData(e.currentTarget);
              submit({
                section,
                action: "save",
                record_id: editing.id,
                branch: form.get("branch"),
                organization: form.get("organization"),
                name: form.get("name"),
                sort_order: form.get("sort_order"),
                ...(form.get("is_active") ? { is_active: "on" } : {}),
              });
            }}
          >
            <div className="modal-head">
              <div>
                <span>{tr(title)}</span>
                <h3>{tr(editing.id ? "Редактирование" : "Новая запись")}</h3>
              </div>
              <button type="button" onClick={() => setEditing(null)}>
                ×
              </button>
            </div>
            {!boot.user.is_organization_manager &&
              !boot.user.is_branch_manager && (
                <label>
                  {tr("Филиал")}
                  <select
                    name="branch"
                    defaultValue={editing.branch_id}
                    required
                  >
                    <option value="">{tr("Выберите филиал")}</option>
                    {data.branches.map((x) => (
                      <option key={x.id} value={x.id}>
                        {x.name}
                      </option>
                    ))}
                  </select>
                </label>
              )}
            {!boot.user.is_organization_manager && (
              <label>
                {tr("Организация")}
                <select
                  name="organization"
                  defaultValue={editing.organization_id}
                  required
                >
                  <option value="">{tr("Выберите организацию")}</option>
                  {data.organizations.map((x) => (
                    <option key={x.id} value={x.id}>
                      {x.name} — {x.branch_name}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <label>
              {tr("Название")}
              <input name="name" defaultValue={editing.name} required />
            </label>
            <label>
              {tr("Сортировка")}
              <input
                type="number"
                min="0"
                name="sort_order"
                defaultValue={editing.sort_order}
              />
            </label>
            <label className="check">
              <input
                type="checkbox"
                name="is_active"
                defaultChecked={editing.is_active}
              />{" "}
              {tr("Активно")}
            </label>
            <div className="modal-actions">
              <button type="button" onClick={() => setEditing(null)}>
                {tr("Отмена")}
              </button>
              <button className="primary-button" disabled={busy}>
                {tr(busy ? "Сохранение…" : "Сохранить")}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

function embeddedUrl(url) {
  if (!url) return "";
  return `${url}${url.includes("?") ? "&" : "?"}embedded=1`;
}

function syncEmbeddedTheme(event) {
  try {
    event.currentTarget.contentDocument.documentElement.dataset.theme =
      window.localStorage.getItem("mtu-react-theme") || "dark";
  } catch (_) {
    /* same-origin frame may still be loading */
  }
}

function ModulePage({ boot, moduleKey }) {
  const tr = createTranslator(boot.language);
  const meta = moduleMeta[moduleKey] || {
    title: "Раздел",
    subtitle: "Рабочая область",
    icon: Settings2,
  };
  const url = boot.legacy_links[moduleKey];
  if (!url) return <Navigate to="/" />;
  return (
    <div className="module-page">
      <iframe
        title={tr(meta.title)}
        src={embeddedUrl(url)}
        onLoad={syncEmbeddedTheme}
      />
    </div>
  );
}

function RequestEditorPage({ language }) {
  const tr = createTranslator(language);
  const { id } = useParams();
  return (
    <div className="module-page with-heading">
      <div className="module-heading">
        <ClipboardList />
        <div>
          <h2>
            {tr("Заявки")} #{id}
          </h2>
          <p>{tr("Редактирование и обработка заявки")}</p>
        </div>
      </div>
      <iframe
        title={`${tr("Заявки")} ${id}`}
        src={embeddedUrl(`/${language || "ru"}/requests/${id}/edit/`)}
        onLoad={syncEmbeddedTheme}
      />
    </div>
  );
}

export default function App({ config }) {
  const {
    loading,
    data: boot,
    error,
    reload,
  } = useRemote(() => api("/api/react/bootstrap/"), []);
  useEffect(() => {
    if (error && error.includes("Доступ запрещён")) {
      const next = `${window.location.pathname}${window.location.search}`;
      window.location.replace(
        `/app/login/?lang=ru&next=${encodeURIComponent(next)}`,
      );
    }
  }, [error]);
  if (loading || (error && error.includes("Доступ запрещён")))
    return <Loading />;
  if (error) return <ErrorState message={error} retry={reload} />;
  return (
    <Layout boot={boot} config={config}>
      <Routes>
        <Route path="/" element={<Dashboard boot={boot} />} />
        <Route
          path="/requests"
          element={
            boot.permissions.requests ? (
              <RequestsPage language={boot.language} />
            ) : (
              <Navigate to="/" />
            )
          }
        />
        <Route
          path="/requests/:id/edit"
          element={
            boot.permissions.requests ? (
              <RequestEditorPage language={boot.language} />
            ) : (
              <Navigate to="/" />
            )
          }
        />
        <Route
          path="/directories/stations"
          element={
            boot.permissions.directories ? (
              <DirectoryPage kind="stations" boot={boot} />
            ) : (
              <Navigate to="/" />
            )
          }
        />
        <Route
          path="/directories/positions"
          element={
            boot.permissions.directories ? (
              <DirectoryPage kind="positions" boot={boot} />
            ) : (
              <Navigate to="/" />
            )
          }
        />
        <Route
          path="/modules/:moduleKey"
          element={<ModuleRoute boot={boot} />}
        />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Layout>
  );
}

function ModuleRoute({ boot }) {
  const { moduleKey } = useParams();
  return <ModulePage boot={boot} moduleKey={moduleKey} />;
}
