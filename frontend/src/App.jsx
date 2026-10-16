import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  NavLink,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import {
  BarChart3,
  Bell,
  Building2,
  CheckCircle2,
  ClipboardList,
  Code2,
  Download,
  FileText,
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
  Quote,
  ScrollText,
  Search,
  Settings2,
  SlidersHorizontal,
  Star,
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
const requestListCache = new Map();
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
  documents: {
    title: "Документы",
    subtitle: "Корпоративные документы",
    icon: FileText,
  },
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
  const tr = useMemo(() => createTranslator(boot.language), [boot.language]);
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
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searchBusy, setSearchBusy] = useState(false);
  const [installPrompt, setInstallPrompt] = useState(null);
  const [pwaHelpOpen, setPwaHelpOpen] = useState(false);
  const [favoriteLinks, setFavoriteLinks] = useState(() => {
    try { return JSON.parse(window.localStorage.getItem("mtu-favorite-links") || "[]"); } catch { return []; }
  });
  const [notifications, setNotifications] = useState(boot.notifications || { unread: 0, items: [] });
  const [permissionPromptOpen, setPermissionPromptOpen] = useState(false);
  const knownNotificationIds = useRef(new Set((boot.notifications?.items || []).map((item) => item.id)));
  const location = useLocation();
  const routeCategory =
    location.pathname.startsWith("/requests") ||
    /^\/modules\/(tasks|documents)/.test(location.pathname)
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
  const currentFavoriteKey = `${location.pathname}${location.search}`;
  const isCurrentFavorite = favoriteLinks.some((item) => item.url === currentFavoriteKey);
  const toggleCurrentFavorite = () => {
    const next = isCurrentFavorite
      ? favoriteLinks.filter((item) => item.url !== currentFavoriteKey)
      : [...favoriteLinks, { url: currentFavoriteKey, title: currentTitle }].slice(-8);
    setFavoriteLinks(next);
    window.localStorage.setItem("mtu-favorite-links", JSON.stringify(next));
  };
  const installPwa = async () => {
    if (!installPrompt) { setPwaHelpOpen(!pwaHelpOpen); return; }
    await installPrompt.prompt();
    await installPrompt.userChoice;
    setInstallPrompt(null);
  };
  useEffect(() => {
    setOpen(false);
  }, [location.pathname]);
  useEffect(() => {
    const rememberInstall = (event) => { event.preventDefault(); setInstallPrompt(event); };
    window.addEventListener("beforeinstallprompt", rememberInstall);
    return () => window.removeEventListener("beforeinstallprompt", rememberInstall);
  }, []);
  useEffect(() => {
    const query = searchQuery.trim();
    if (query.length < 2) { setSearchResults([]); setSearchBusy(false); return undefined; }
    setSearchBusy(true);
    const timer = window.setTimeout(() => {
      api(`/api/react/search/?q=${encodeURIComponent(query)}`)
        .then((data) => setSearchResults(data.results || []))
        .catch(() => setSearchResults([]))
        .finally(() => setSearchBusy(false));
    }, 260);
    return () => window.clearTimeout(timer);
  }, [searchQuery]);
  useEffect(() => {
    setNavCategory(routeCategory);
  }, [routeCategory]);
  useEffect(() => {
    document.documentElement.lang = boot.language || "ru";
  }, [boot.language]);
  useEffect(() => {
    if (!boot.site?.favicon_url) return;
    let icon = document.querySelector("link[rel='icon']");
    if (!icon) {
      icon = document.createElement("link");
      icon.rel = "icon";
      document.head.appendChild(icon);
    }
    icon.href = boot.site.favicon_url;
  }, [boot.site?.favicon_url]);
  useEffect(() => {
    if (!boot.user) return undefined;
    const heartbeat = () => {
      if (document.visibilityState === "visible") {
        api("/api/presence/heartbeat/", { method: "POST" }).catch(() => {});
      }
    };
    heartbeat();
    const timer = window.setInterval(heartbeat, 20000);
    document.addEventListener("visibilitychange", heartbeat);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", heartbeat);
    };
  }, [boot.user]);
  useEffect(() => {
    if (!("Notification" in window) || window.Notification.permission !== "default") return undefined;
    const remindAfter = Number(window.localStorage.getItem("mtu-notification-remind-after") || 0);
    if (remindAfter > Date.now()) return undefined;
    const timer = window.setTimeout(() => setPermissionPromptOpen(true), 1200);
    return () => window.clearTimeout(timer);
  }, []);
  useEffect(() => {
    const refreshNotifications = () => {
      api("/api/notifications/requests/").then((updated) => {
        const newItems = updated.items.filter((item) => !knownNotificationIds.current.has(item.id));
        updated.items.forEach((item) => knownNotificationIds.current.add(item.id));
        setNotifications(updated);
        if (window.Notification?.permission === "granted") {
          newItems.reverse().forEach((item) => {
            const alert = new window.Notification(item.title, {
              body: item.message || tr("Откройте центр уведомлений, чтобы посмотреть подробности."),
              icon: boot.site?.favicon_url || "/static/img/favicon.svg",
              tag: `request-${item.id}`,
            });
            alert.onclick = () => {
              window.focus();
              window.location.href = item.url;
              alert.close();
            };
          });
        }
      }).catch(() => {});
    };
    const timer = window.setInterval(refreshNotifications, 15000);
    return () => window.clearInterval(timer);
  }, [boot.site?.favicon_url, tr]);
  const postponeNotifications = () => {
    window.localStorage.setItem("mtu-notification-remind-after", String(Date.now() + 3 * 24 * 60 * 60 * 1000));
    setPermissionPromptOpen(false);
  };
  const enableBrowserNotifications = async () => {
    if (!("Notification" in window)) return;
    const permission = await window.Notification.requestPermission();
    setPermissionPromptOpen(false);
    if (permission === "granted") {
      window.localStorage.removeItem("mtu-notification-remind-after");
      new window.Notification(tr("Уведомления включены"), {
        body: tr("Теперь вы будете видеть новые события, даже если вкладка свёрнута."),
        icon: boot.site?.favicon_url || "/static/img/favicon.svg",
        tag: "notifications-enabled",
      });
    }
  };
  const markNotificationsRead = async (id = null) => {
    const updated = await api("/api/notifications/requests/", {
      method: "POST",
      body: JSON.stringify(id ? { id } : {}),
    });
    setNotifications(updated);
  };
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
            <img
              src={boot.site.logo_url || "/static/img/mtu-forum-mark.svg"}
              alt={boot.site.name}
              onError={(event) => {
                event.currentTarget.onerror = null;
                event.currentTarget.src = "/static/img/mtu-forum-mark.svg";
              }}
            />
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
              {favoriteLinks.length > 0 && (
                <div className="favorite-nav-links">
                  <small>{tr("ИЗБРАННОЕ")}</small>
                  {favoriteLinks.map((item) => (
                    <NavLink key={item.url} to={item.url}><Star />{item.title}</NavLink>
                  ))}
                </div>
              )}
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
                  {renderModuleLinks(["tasks", "documents"])}
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
            <div className="tool-menu global-search-tool">
              <button type="button" className={`icon-button ${searchOpen ? "active" : ""}`} onClick={() => { setSearchOpen(!searchOpen); setNotificationsOpen(false); setAccessOpen(false); setLanguageOpen(false); }} aria-label={tr("Глобальный поиск")} title={tr("Глобальный поиск")}><Search /></button>
              {searchOpen && (
                <section className="react-popover global-search-popover" aria-label={tr("Глобальный поиск")}>
                  <label><Search /><input autoFocus type="search" value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder={tr("Найти заявку, пользователя, документ или платформу")} /></label>
                  <div className="global-search-results">
                    {searchBusy && <p>{tr("Поиск…")}</p>}
                    {!searchBusy && searchQuery.trim().length >= 2 && !searchResults.length && <p>{tr("Ничего не найдено")}</p>}
                    {searchResults.map((item) => (
                      <a key={item.id} href={item.url} className={`search-result is-${item.type}`}>
                        <i>{item.type === "document" ? <FileText /> : item.type === "platform" ? <ExternalLink /> : item.type === "user" ? <UserCircle /> : <ClipboardList />}</i>
                        <span><strong>{item.title}</strong><small>{item.subtitle}</small></span>
                      </a>
                    ))}
                  </div>
                </section>
              )}
            </div>
            <button type="button" className={`icon-button ${isCurrentFavorite ? "active is-favorite" : ""}`} onClick={toggleCurrentFavorite} aria-label={tr(isCurrentFavorite ? "Удалить из избранного" : "Добавить в избранное")} title={tr(isCurrentFavorite ? "Удалить из избранного" : "Добавить в избранное")}><Star /></button>
            <div className="tool-menu">
              <button type="button" className={`icon-button pwa-install-button ${pwaHelpOpen ? "active" : ""}`} onClick={installPwa} aria-label={tr("Установить приложение")} title={tr("Установить приложение")}><Download /></button>
              {pwaHelpOpen && !installPrompt && <section className="react-popover pwa-help-popover"><strong>{tr("Установить приложение")}</strong><p>{tr("Откройте меню браузера и выберите «Установить приложение» или «Добавить на главный экран».")}</p></section>}
            </div>
            <div className="tool-menu notification-tool">
              <button
                type="button"
                className={`icon-button notification-button ${notificationsOpen ? "active" : ""}`}
                onClick={() => {
                  setNotificationsOpen(!notificationsOpen);
                  setAccessOpen(false);
                  setLanguageOpen(false);
                }}
                aria-label={tr("Уведомления")}
                aria-expanded={notificationsOpen}
              >
                <Bell />
                {notifications.unread > 0 && <b>{Math.min(notifications.unread, 99)}</b>}
              </button>
              {notificationsOpen && (
                <section className="react-popover notification-popover" aria-label={tr("Центр уведомлений")}>
                  <div className="notification-head">
                    <div><small>{tr("СОБЫТИЯ")}</small><strong>{tr("Центр уведомлений")}</strong></div>
                    {notifications.unread > 0 && <button type="button" onClick={() => markNotificationsRead()}>{tr("Прочитать все")}</button>}
                  </div>
                  <div className="notification-list">
                    {notifications.items.map((item) => (
                      <a
                        key={item.id}
                        className={item.is_read ? "" : "unread"}
                        href={item.url}
                        onClick={(event) => {
                          if (!item.is_read) {
                            event.preventDefault();
                            markNotificationsRead(item.id).finally(() => {
                              window.location.href = item.url;
                            });
                          }
                        }}
                      >
                        <i className={`notification-kind is-${item.kind}`}><Bell /></i>
                        <span><strong>{item.title}</strong>{item.message && <small>{item.message}</small>}</span>
                      </a>
                    ))}
                    {!notifications.items.length && <p>{tr("Новых уведомлений нет.")}</p>}
                  </div>
                </section>
              )}
            </div>
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
      {permissionPromptOpen && (
        <div className="browser-notification-backdrop" role="presentation">
          <section className="browser-notification-card" role="dialog" aria-modal="true" aria-labelledby="browser-notification-title">
            <button className="browser-notification-close" type="button" onClick={postponeNotifications} aria-label={tr("Закрыть")}>×</button>
            <div className="browser-notification-bell" aria-hidden="true"><Bell /></div>
            <h2 id="browser-notification-title">{tr("Включите уведомления")}</h2>
            <p>{tr("Разрешите уведомления, чтобы узнавать о новых заявках и изменениях, даже когда вкладка свёрнута.")}</p>
            <div className="browser-notification-actions">
              <button type="button" onClick={postponeNotifications}>{tr("Позже")}</button>
              <button className="primary" type="button" onClick={enableBrowserNotifications}><Bell />{tr("Включить")}</button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

function Activity3DChart({ today = [], done = [], tr }) {
  const values = today.map((row, index) => ({ date: row.date, created: row.value, done: done[index]?.value || 0 }));
  const maximum = Math.max(1, ...values.flatMap((row) => [row.created, row.done]));
  const barHeight = (value) => value > 0 ? Math.max(5, value / maximum * 100) : 0;
  return (
    <article className="analytics-3d-card">
      <header>
        <div><span>{tr("АНАЛИТИКА")}</span><h3>{tr("Динамика за 7 дней")}</h3><p>{tr("Новые и выполненные заявки по дням.")}</p></div>
        <div className="chart-key"><span className="is-new">{tr("Новые")}</span><span className="is-done">{tr("Выполнено")}</span></div>
      </header>
      <div className="columns-3d" role="img" aria-label={tr("Динамика за 7 дней")}>
        {values.map((row) => (
          <div className="column-3d-group" key={row.date}>
            <div className="column-3d-pair">
              <i className={`column-3d is-new ${row.created === 0 ? "is-empty" : ""}`} style={{ "--bar-height": `${barHeight(row.created)}%` }} data-tooltip={`${tr("Новые")}: ${row.created}`} />
              <i className={`column-3d is-done ${row.done === 0 ? "is-empty" : ""}`} style={{ "--bar-height": `${barHeight(row.done)}%` }} data-tooltip={`${tr("Выполнено")}: ${row.done}`} />
            </div>
            <span>{row.date}</span>
          </div>
        ))}
      </div>
    </article>
  );
}

function Platform3DChart({ platforms = [], tr }) {
  const rows = [...platforms].sort((a, b) => b.total - a.total).slice(0, 5);
  const maximum = Math.max(1, ...rows.map((row) => row.total));
  return (
    <article className="analytics-3d-card">
      <header><div><span>{tr("АНАЛИТИКА")}</span><h3>{tr("Распределение по платформам")}</h3><p>{tr("Сравнение количества заявок по платформам.")}</p></div></header>
      <div className="platform-bars-3d">
        {rows.map((row, index) => (
          <div className="platform-bar-3d-row" key={row.name} title={`${row.name}: ${row.total}`}>
            <span>{row.name}</span>
            <div>
              <i className="platform-stack-3d" style={{ "--bar-width": `${Math.max(4, row.total / maximum * 100)}%`, "--bar-index": index }}>
                <b className="is-done" style={{ flex: row.done }} title={`${tr("Выполнено")}: ${row.done}`} />
                <b className="is-new" style={{ flex: Math.max(0, row.total - row.done - row.blocked) }} title={`${tr("Новые")}: ${Math.max(0, row.total - row.done - row.blocked)}`} />
                <b className="is-blocked" style={{ flex: row.blocked }} title={`${tr("Заблокировано")}: ${row.blocked}`} />
              </i>
            </div>
            <strong>{row.total}</strong>
          </div>
        ))}
        {!rows.length && <p>{tr("Нет доступных платформ.")}</p>}
      </div>
    </article>
  );
}

const dashboardQuotes = {
  ru: [
    { text: "Сила — в справедливости.", author: "Амир Темур" },
    { text: "Если ты человек, не называй человеком того, кого не заботит горе народа.", author: "Алишер Навои" },
    { text: "Кто не владеет своим языком, тот не заслуживает внимания народа.", author: "Алишер Навои" },
    { text: "Воспитание для нас — вопрос жизни или смерти, спасения или гибели, счастья или бедствия.", author: "Абдулла Авлони" },
    { text: "Знание — плод повторения и возвращения к изученному.", author: "Абу Райхан Беруни" },
    { text: "Доброе слово — пища душе.", author: "Узбекская народная мудрость" },
    { text: "Знание открывает путь, труд доводит до цели.", author: "Узбекская народная мудрость" },
    { text: "Совет мудрого сокращает долгую дорогу.", author: "Узбекская народная мудрость" },
    { text: "Терпение приносит плод, поспешность — сожаление.", author: "Узбекская народная мудрость" },
    { text: "Человек ценен не словами, а полезными делами.", author: "Узбекская народная мудрость" },
    { text: "Где есть согласие, там есть сила.", author: "Узбекская народная мудрость" },
    { text: "Время — самый справедливый наставник.", author: "Узбекская народная мудрость" },
    { text: "Учись у прошлого, трудись сегодня, думай о будущем.", author: "Узбекская народная мудрость" },
    { text: "Малое добро открывает большие двери.", author: "Узбекская народная мудрость" },
    { text: "Ум растёт от вопросов, мастерство — от практики.", author: "Узбекская народная мудрость" },
    { text: "Честный труд украшает человека.", author: "Узбекская народная мудрость" },
    { text: "Порядок в деле начинается с порядка в мыслях.", author: "Узбекская народная мудрость" },
    { text: "Дорогу осилит тот, кто продолжает идти.", author: "Узбекская народная мудрость" },
  ],
  uz: [
    { text: "Kuch — adolatda.", author: "Amir Temur" },
    { text: "Odami ersang, demagil odami, onikim yo‘q xalq g‘amidin g‘ami.", author: "Alisher Navoiy" },
    { text: "Tilga ixtiyorsiz — elga e’tiborsiz.", author: "Alisher Navoiy" },
    { text: "Tarbiya biz uchun yo hayot — yo mamot, yo najot — yo halokat, yo saodat — yo falokat masalasidir.", author: "Abdulla Avloniy" },
    { text: "Bilim — qaytarish va takrorlash mevasidir.", author: "Abu Rayhon Beruniy" },
    { text: "Yaxshi so‘z — jon ozig‘i.", author: "O‘zbek xalq maqoli" },
    { text: "Bilim yo‘l ochar, mehnat manzilga yetkazar.", author: "O‘zbek xalq hikmati" },
    { text: "Dononing maslahati uzoq yo‘lni qisqartirar.", author: "O‘zbek xalq hikmati" },
    { text: "Sabr meva keltirar, shoshqaloqlik — pushaymon.", author: "O‘zbek xalq hikmati" },
    { text: "Inson so‘zi bilan emas, foydali ishi bilan qadrlanadi.", author: "O‘zbek xalq hikmati" },
    { text: "Hamjihatlik bor joyda kuch bor.", author: "O‘zbek xalq hikmati" },
    { text: "Vaqt — eng adolatli ustoz.", author: "O‘zbek xalq hikmati" },
    { text: "O‘tmishdan o‘rgan, bugun mehnat qil, kelajakni o‘yla.", author: "O‘zbek xalq hikmati" },
    { text: "Kichik yaxshilik katta eshiklarni ochar.", author: "O‘zbek xalq hikmati" },
    { text: "Aql savoldan, mahorat mashqdan o‘sadi.", author: "O‘zbek xalq hikmati" },
    { text: "Halol mehnat insonni bezaydi.", author: "O‘zbek xalq hikmati" },
    { text: "Ishdagi tartib fikrdagi tartibdan boshlanadi.", author: "O‘zbek xalq hikmati" },
    { text: "Yo‘lni davom etgan odam bosib o‘tadi.", author: "O‘zbek xalq hikmati" },
  ],
  "uz-cyrl": [
    { text: "Куч — адолатда.", author: "Амир Темур" },
    { text: "Одами эрсанг, демагил одами, ониким йўқ халқ ғамидин ғами.", author: "Алишер Навоий" },
    { text: "Тилга ихтиёрсиз — элга эътиборсиз.", author: "Алишер Навоий" },
    { text: "Тарбия биз учун ё ҳаёт — ё мамот, ё нажот — ё ҳалокат, ё саодат — ё фалокат масаласидир.", author: "Абдулла Авлоний" },
    { text: "Билим — қайтариш ва такрорлаш мевасидир.", author: "Абу Райҳон Беруний" },
    { text: "Яхши сўз — жон озиғи.", author: "Ўзбек халқ мақоли" },
    { text: "Билим йўл очар, меҳнат манзилга етказар.", author: "Ўзбек халқ ҳикмати" },
    { text: "Дононинг маслаҳати узоқ йўлни қисқартирар.", author: "Ўзбек халқ ҳикмати" },
    { text: "Сабр мева келтирар, шошқалоқлик — пушаймон.", author: "Ўзбек халқ ҳикмати" },
    { text: "Инсон сўзи билан эмас, фойдали иши билан қадрланади.", author: "Ўзбек халқ ҳикмати" },
    { text: "Ҳамжиҳатлик бор жойда куч бор.", author: "Ўзбек халқ ҳикмати" },
    { text: "Вақт — энг адолатли устоз.", author: "Ўзбек халқ ҳикмати" },
    { text: "Ўтмишдан ўрган, бугун меҳнат қил, келажакни ўйла.", author: "Ўзбек халқ ҳикмати" },
    { text: "Кичик яхшилик катта эшикларни очар.", author: "Ўзбек халқ ҳикмати" },
    { text: "Ақл саволдан, маҳорат машқдан ўсади.", author: "Ўзбек халқ ҳикмати" },
    { text: "Ҳалол меҳнат инсонни безайди.", author: "Ўзбек халқ ҳикмати" },
    { text: "Ишдаги тартиб фикрдаги тартибдан бошланади.", author: "Ўзбек халқ ҳикмати" },
    { text: "Йўлни давом этган одам босиб ўтади.", author: "Ўзбек халқ ҳикмати" },
  ],
  en: [
    { text: "Strength lies in justice.", author: "Amir Temur" },
    { text: "Call no one human who feels no concern for the people’s sorrow.", author: "Alisher Navoi" },
    { text: "One who cannot govern their tongue shows no regard for the people.", author: "Alisher Navoi" },
    { text: "Education is for us a matter of life or death, salvation or ruin, happiness or disaster.", author: "Abdulla Avloni" },
    { text: "Knowledge is the fruit of returning to and repeating what has been learned.", author: "Abu Rayhan Beruni" },
    { text: "A kind word is nourishment for the soul.", author: "Uzbek proverb" },
    { text: "Knowledge opens the road; work carries you to the destination.", author: "Uzbek wisdom" },
    { text: "Wise advice shortens a long road.", author: "Uzbek wisdom" },
    { text: "Patience bears fruit; haste brings regret.", author: "Uzbek wisdom" },
    { text: "A person is valued by useful deeds, not words.", author: "Uzbek wisdom" },
    { text: "Where there is unity, there is strength.", author: "Uzbek wisdom" },
    { text: "Time is the fairest teacher.", author: "Uzbek wisdom" },
    { text: "Learn from the past, work today, and think of the future.", author: "Uzbek wisdom" },
    { text: "A small kindness opens great doors.", author: "Uzbek wisdom" },
    { text: "The mind grows through questions; skill grows through practice.", author: "Uzbek wisdom" },
    { text: "Honest work adorns a person.", author: "Uzbek wisdom" },
    { text: "Order in work begins with order in thought.", author: "Uzbek wisdom" },
    { text: "The road is completed by the one who keeps moving.", author: "Uzbek wisdom" },
  ],
};

function pickFreshQuote(language, length) {
  if (!length) return 0;
  const key = `mtu-last-quote-${language}`;
  let previous = -1;
  try { previous = Number(window.sessionStorage.getItem(key)); } catch { previous = -1; }
  let next = Math.floor(Math.random() * length);
  if (length > 1 && next === previous) next = (next + 1 + Math.floor(Math.random() * (length - 1))) % length;
  try { window.sessionStorage.setItem(key, String(next)); } catch { /* The quote still changes without storage. */ }
  return next;
}

function AnimatedAiAssistant({ mood, hint, tr, permissions, navigate }) {
  const [open, setOpen] = useState(false);
  const assistantRef = useRef(null);
  const trackPointer = (event) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - bounds.left) / bounds.width - 0.5) * 2;
    const y = ((event.clientY - bounds.top) / bounds.height - 0.5) * 2;
    assistantRef.current?.style.setProperty("--look-x", x.toFixed(2));
    assistantRef.current?.style.setProperty("--look-y", y.toFixed(2));
  };
  const resetPointer = () => {
    assistantRef.current?.style.setProperty("--look-x", "0");
    assistantRef.current?.style.setProperty("--look-y", "0");
  };
  const go = (path) => {
    setOpen(false);
    navigate(path);
  };
  return (
    <div
      ref={assistantRef}
      className={`ai-assistant ai-assistant--${mood}${open ? " is-open" : ""}`}
      onMouseMove={trackPointer}
      onMouseLeave={resetPointer}
    >
      <div className="ai-assistant__hint" role="status">{hint}</div>
      <span className="ai-assistant__orbit"><i /><i /><i /></span>
      <span className="ai-assistant__antenna"><i /></span>
      <button
        className="ai-assistant__head"
        type="button"
        aria-label={tr("Открыть AI-помощника")}
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <span className="ai-assistant__screen">
          <i className="ai-assistant__eye ai-assistant__eye--left" />
          <i className="ai-assistant__eye ai-assistant__eye--right" />
          <i className="ai-assistant__smile" />
          <i className="ai-assistant__scan" />
        </span>
        <i className="ai-assistant__ear ai-assistant__ear--left" />
        <i className="ai-assistant__ear ai-assistant__ear--right" />
      </button>
      <span className="ai-assistant__badge"><i />AI</span>
      {open && (
        <div className="ai-assistant__menu">
          <strong>{tr("Быстрые действия")}</strong>
          {permissions.requests && <button type="button" onClick={() => go("/requests?status=new")}><ClipboardList />{tr("Новые заявки")}</button>}
          {permissions.requests && <button type="button" onClick={() => { setOpen(false); document.querySelector(".sla-panel")?.scrollIntoView({ behavior: "smooth", block: "start" }); }}><Bell />{tr("Просроченные заявки")}</button>}
          {permissions.chats && <button type="button" onClick={() => go("/modules/chats")}><MessageCircle />{tr("Открыть чаты")}</button>}
          {permissions.users && <button type="button" onClick={() => go("/modules/users")}><Users />{tr("Найти сотрудника")}</button>}
        </div>
      )}
    </div>
  );
}

function Dashboard({ boot }) {
  const tr = createTranslator(boot.language);
  const navigate = useNavigate();
  const [activeChartSegment, setActiveChartSegment] = useState(null);
  const [dashboardSettingsOpen, setDashboardSettingsOpen] = useState(false);
  const [webPlatforms, setWebPlatforms] = useState(boot.dashboard.web_platforms || []);
  const [widgets, setWidgets] = useState(() => {
    try { return { intro: true, metrics: true, sla: true, analytics: true, services: true, ...JSON.parse(window.localStorage.getItem("mtu-dashboard-widgets") || "{}") }; }
    catch { return { intro: true, metrics: true, sla: true, analytics: true, services: true }; }
  });
  const toggleWidget = (key) => {
    const next = { ...widgets, [key]: !widgets[key] };
    setWidgets(next);
    window.localStorage.setItem("mtu-dashboard-widgets", JSON.stringify(next));
  };
  const togglePlatformFavorite = async (platform) => {
    const result = await api(`/api/react/favorites/platform/${platform.id}/`, { method: "POST" });
    setWebPlatforms((current) => current.map((item) => item.id === platform.id ? { ...item, favorite: result.favorite } : item));
  };
  const quotes = dashboardQuotes[boot.language] || dashboardQuotes.ru;
  const quoteLanguageRef = useRef(boot.language);
  const [quoteIndex, setQuoteIndex] = useState(() => pickFreshQuote(boot.language, quotes.length));
  const [remoteQuote, setRemoteQuote] = useState(null);
  useEffect(() => {
    if (quoteLanguageRef.current !== boot.language) {
      quoteLanguageRef.current = boot.language;
      setQuoteIndex(pickFreshQuote(boot.language, quotes.length));
    }
    let active = true;
    setRemoteQuote(null);
    const loadQuote = () => {
      api(`/api/react/quote/?lang=${encodeURIComponent(boot.language)}&_=${Date.now()}`)
        .then((result) => {
          if (!active) return;
          if (!result.ok || !result.quote?.text) {
            setRemoteQuote(null);
            setQuoteIndex(pickFreshQuote(boot.language, quotes.length));
            return;
          }
          setRemoteQuote(result.quote);
        })
        .catch(() => {
          if (!active) return;
          setRemoteQuote(null);
          setQuoteIndex((index) => (quotes.length > 1 ? (index + 1) % quotes.length : index));
        });
    };
    loadQuote();
    const quoteTimer = window.setInterval(loadQuote, 30000);
    return () => {
      active = false;
      window.clearInterval(quoteTimer);
    };
  }, [boot.language, quotes.length]);
  const shownQuote = remoteQuote || quotes[quoteIndex];
  const stats = boot.dashboard.stats;
  const overdueCount = boot.dashboard.sla?.overdue || 0;
  const dueSoonCount = boot.dashboard.sla?.due_soon || 0;
  const assistantMood = overdueCount > 0 ? "danger" : dueSoonCount > 0 ? "warning" : "healthy";
  const assistantHint = overdueCount > 0
    ? tr("Просрочено заявок: {count}", { count: overdueCount })
    : dueSoonCount > 0
      ? tr("До срока менее 24 часов: {count}", { count: dueSoonCount })
      : stats.new > 0
        ? tr("Новые заявки: {count}", { count: stats.new })
        : tr("Все системы работают стабильно.");
  const currentHour = new Date().getHours();
  const greetingKey = currentHour < 12
    ? "Доброе утро, {name}"
    : currentHour < 18
      ? "Добрый день, {name}"
      : "Добрый вечер, {name}";
  const formatDuration = (seconds) => {
    if (!seconds) return "—";
    if (seconds < 3600) return `${Math.max(1, Math.round(seconds / 60))} ${tr("мин.")}`;
    if (seconds < 86400) return `${Math.round(seconds / 3600)} ${tr("ч.")}`;
    return `${Math.round(seconds / 86400)} ${tr("дн.")}`;
  };
  const requestTotal = stats.new + stats.done + stats.blocked;
  const requestChart = [
    { key: "new", label: tr("Новые заявки"), value: stats.new },
    { key: "done", label: tr("Выполнено"), value: stats.done },
    { key: "blocked", label: tr("Заблокировано"), value: stats.blocked },
  ].map((item) => ({
    ...item,
    percent: requestTotal ? Math.round((item.value / requestTotal) * 100) : 0,
  }));
  const newEnd = requestTotal ? (stats.new / requestTotal) * 360 : 0;
  const doneEnd = requestTotal
    ? ((stats.new + stats.done) / requestTotal) * 360
    : 0;
  const inspectChartSegment = (event) => {
    if (!requestTotal) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - bounds.left;
    const y = event.clientY - bounds.top;
    const dx = x - bounds.width / 2;
    const dy = y - bounds.height / 2;
    const distance = Math.hypot(dx, dy);
    if (distance < bounds.width * 0.33 || distance > bounds.width * 0.5) {
      setActiveChartSegment(null);
      return;
    }
    const angle = (Math.atan2(dy, dx) * 180 / Math.PI + 450) % 360;
    const item = angle < newEnd
      ? requestChart[0]
      : angle < doneEnd
        ? requestChart[1]
        : requestChart[2];
    setActiveChartSegment({ ...item, x, y });
  };
  return (
    <div className="page-stack">
      <div className="dashboard-customize-bar">
        <span>{tr("Настройте Dashboard под свою работу")}</span>
        <button type="button" onClick={() => setDashboardSettingsOpen(!dashboardSettingsOpen)}><SlidersHorizontal />{tr("Настроить блоки")}</button>
        {dashboardSettingsOpen && (
          <div className="dashboard-widget-picker">
            {[["intro", "Приветствие и цитата"], ["metrics", "Основные показатели"], ["sla", "SLA-контроль"], ["analytics", "Аналитика"], ["services", "WEB-платформы"]].map(([key, label]) => (
              <label key={key}><input type="checkbox" checked={widgets[key]} onChange={() => toggleWidget(key)} /><span>{tr(label)}</span></label>
            ))}
          </div>
        )}
      </div>
      {widgets.intro && (
      <section className="dashboard-intro-grid">
        <article className="hero">
          <div>
            <span>{tr("ОБЗОР СИСТЕМЫ")}</span>
            <h2>
              {tr(greetingKey, {
                name: boot.user.first_name || boot.user.username,
              })}
            </h2>
            <p>
              {tr(
                "Актуальное состояние заявок и быстрый доступ к рабочим сервисам.",
              )}
            </p>
          </div>
          <AnimatedAiAssistant
            mood={assistantMood}
            hint={assistantHint}
            tr={tr}
            permissions={boot.permissions}
            navigate={navigate}
          />
        </article>
        <article className="quote-card" aria-live="polite">
          <div className="quote-card-head">
            <span>{tr("МЫСЛЬ ДНЯ")}</span>
            <Quote aria-hidden="true" />
          </div>
          <blockquote>“{shownQuote.text}”</blockquote>
          <div className="quote-card-footer">
            <cite>{shownQuote.author}</cite>
          </div>
        </article>
      </section>
      )}
      {boot.permissions.requests && (
        <>
          {widgets.metrics && (
          <section className="metric-grid">
            <article>
              <span>{tr("Заявки сегодня")}</span>
              <strong>{stats.today ?? 0}</strong>
              <ClipboardList />
            </article>
            <article>
              <span>{tr("Среднее время обработки")}</span>
              <strong>{formatDuration(stats.average_processing_seconds)}</strong>
              <CheckCircle2 />
            </article>
            <article className="online-users-metric">
              <span>{tr("Пользователи онлайн")}</span>
              <strong>{stats.online ?? 0}</strong>
              {boot.dashboard.online_users?.length ? (
                <div className="online-user-avatars" aria-label={tr("Пользователи онлайн")}>
                  {boot.dashboard.online_users.slice(0, 4).map((onlineUser) => (
                    <span
                      className="online-user-avatar"
                      key={onlineUser.id}
                      tabIndex="0"
                      role="img"
                      aria-label={onlineUser.name}
                      data-name={onlineUser.name}
                    >
                      {onlineUser.avatar_url ? (
                        <img src={onlineUser.avatar_url} alt="" />
                      ) : (
                        <b>{onlineUser.initials}</b>
                      )}
                    </span>
                  ))}
                  {boot.dashboard.online_users.length > 4 && (
                    <span className="online-user-more" aria-label={tr("Ещё {count}", { count: boot.dashboard.online_users.length - 4 })}>
                      +{boot.dashboard.online_users.length - 4}
                    </span>
                  )}
                </div>
              ) : (
                <Users />
              )}
            </article>
            <article>
              <span>{tr("Непрочитанные чаты")}</span>
              <strong>{stats.chats}</strong>
              <MessageCircle />
            </article>
          </section>
          )}
          {widgets.sla && (
          <section className="sla-panel">
            <div className="sla-heading">
              <div><span>{tr("КОНТРОЛЬ SLA")}</span><h2>{tr("Сроки обработки заявок")}</h2><p>{tr("Ближайшие сроки и просроченные заявки.")}</p></div>
              <div className="sla-summary">
                <span className="overdue"><b>{boot.dashboard.sla?.overdue || 0}</b>{tr("Просрочено")}</span>
                <span className="soon"><b>{boot.dashboard.sla?.due_soon || 0}</b>{tr("До 24 часов")}</span>
              </div>
            </div>
            <div className="sla-list">
              {(boot.dashboard.sla?.items || []).map((item) => {
                const seconds = Math.abs(item.remaining_seconds);
                const days = Math.floor(seconds / 86400);
                const hours = Math.floor((seconds % 86400) / 3600);
                const minutes = Math.max(1, Math.floor((seconds % 3600) / 60));
                const timeLabel = [
                  days ? `${days} ${tr("дн.")}` : "",
                  hours ? `${hours} ${tr("ч.")}` : "",
                  !days && (!hours || minutes) ? `${minutes} ${tr("мин.")}` : "",
                ].filter(Boolean).join(" ");
                return (
                  <a href={item.edit_url} key={item.id} className={item.overdue ? "overdue" : ""}>
                    <span>#{item.id}</span>
                    <div><strong>{item.title}</strong><small>{item.assignee || tr("Исполнитель не назначен")}{item.company ? ` · ${item.company}` : ""}</small></div>
                    <b>{timeLabel}</b>
                  </a>
                );
              })}
              {!boot.dashboard.sla?.items?.length && <p>{tr("Активных сроков SLA нет.")}</p>}
            </div>
          </section>
          )}
          {widgets.analytics && (
          <>
          <section className="request-chart-panel" aria-label={tr("Статистика заявок")}>
            <div className="request-chart-copy">
              <span>{tr("ОБЗОР СИСТЕМЫ")}</span>
              <h2>{tr("Статистика заявок")}</h2>
              <p>{tr("Распределение текущих заявок по статусам.")}</p>
              <div className="request-chart-legend">
                {requestChart.map((item) => (
                  <div className={`request-chart-row is-${item.key}`} key={item.key}>
                    <div>
                      <i aria-hidden="true" />
                      <span>{item.label}</span>
                      <strong>{item.value}</strong>
                      <b>{item.percent}%</b>
                    </div>
                    <span className="request-chart-track" aria-hidden="true">
                      <i style={{ width: `${item.percent}%` }} />
                    </span>
                  </div>
                ))}
              </div>
            </div>
            <div
              className={`request-donut ${requestTotal ? "" : "is-empty"}`}
              style={{
                "--chart-new-end": `${newEnd}deg`,
                "--chart-done-end": `${doneEnd}deg`,
              }}
              role="img"
              aria-label={`${tr("Всего")}: ${requestTotal}`}
              onPointerMove={inspectChartSegment}
              onPointerLeave={() => setActiveChartSegment(null)}
            >
              <div>
                <small>{activeChartSegment?.label || tr("Всего")}</small>
                <strong>{activeChartSegment?.value ?? requestTotal}</strong>
                <span>{tr("Заявки")}</span>
              </div>
              {activeChartSegment && (
                <output
                  className={`request-chart-tooltip is-${activeChartSegment.key}`}
                  style={{ left: activeChartSegment.x, top: activeChartSegment.y }}
                >
                  <b>{activeChartSegment.label}</b>
                  <span>{activeChartSegment.value} · {activeChartSegment.percent}%</span>
                </output>
              )}
            </div>
          </section>
          <section className="analytics-3d-grid">
            <Activity3DChart today={boot.dashboard.activity?.today || []} done={boot.dashboard.activity?.done || []} tr={tr} />
            <Platform3DChart platforms={boot.dashboard.platforms} tr={tr} />
          </section>
          </>
          )}
        </>
      )}
      {widgets.services && (
      <section className="panel">
        <div className="panel-head">
          <div>
            <span>{tr("БЫСТРЫЙ ДОСТУП")}</span>
            <h2>{tr("WEB-платформы")}</h2>
          </div>
        </div>
        <div className="service-grid">
          {[...webPlatforms].sort((a, b) => Number(b.favorite) - Number(a.favorite)).map((item) => (
            <article className={`service-favorite-card ${item.favorite ? "is-favorite" : ""}`} key={item.id}>
              <button type="button" onClick={() => togglePlatformFavorite(item)} aria-label={tr(item.favorite ? "Удалить из избранного" : "Добавить в избранное")} title={tr(item.favorite ? "Удалить из избранного" : "Добавить в избранное")}><Star /></button>
              <a href={item.open_url} target="_blank" rel="noreferrer">
                <div>{item.image_url ? <img src={item.image_url} /> : "WEB"}</div>
                <strong>{item.name}</strong>
                <small>{item.uses} {tr("открытий")}</small>
              </a>
            </article>
          ))}
        </div>
      </section>
      )}
    </div>
  );
}

function RequestsPage({ language }) {
  const tr = createTranslator(language);
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(() => searchParams.get("q") || "");
  const [status, setStatus] = useState(() => searchParams.get("status") || "");
  const [platform, setPlatform] = useState(() => searchParams.get("platform") || "");
  const [company, setCompany] = useState(() => searchParams.get("company") || "");
  const [position, setPosition] = useState(() => searchParams.get("position") || "");
  const [revealed, setRevealed] = useState(new Set());
  const [revealedValues, setRevealedValues] = useState({});
  const [confirmSecret, setConfirmSecret] = useState(null);
  const [confirmPassword, setConfirmPassword] = useState("");
  const [confirmError, setConfirmError] = useState("");
  const [confirmBusy, setConfirmBusy] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);
  const endpoint = `/api/dashboard/requests/?q=${encodeURIComponent(query)}&status=${encodeURIComponent(status)}&platform=${encodeURIComponent(platform)}&company=${encodeURIComponent(company)}&position=${encodeURIComponent(position)}`;
  const cachedRequests = requestListCache.get(endpoint) || null;
  const [requestState, setRequestState] = useState(() => ({
    loading: !cachedRequests,
    data: cachedRequests,
    error: "",
  }));
  useEffect(() => {
    let active = true;
    const cached = requestListCache.get(endpoint) || null;
    setRequestState({ loading: !cached, data: cached, error: "" });
    api(endpoint)
      .then((result) => {
        if (!active) return;
        requestListCache.set(endpoint, result);
        setRequestState({ loading: false, data: result, error: "" });
      })
      .catch((requestError) => {
        if (!active) return;
        setRequestState((current) => ({
          ...current,
          loading: false,
          error: requestError.message,
        }));
      });
    return () => {
      active = false;
    };
  }, [endpoint, reloadToken]);
  const { loading, data, error } = requestState;
  const reload = () => setReloadToken((value) => value + 1);
  useEffect(() => {
    const next = {};
    if (query) next.q = query;
    if (status) next.status = status;
    if (platform) next.platform = platform;
    if (company) next.company = company;
    if (position) next.position = position;
    setSearchParams(next, { replace: true });
  }, [query, status, platform, company, position, setSearchParams]);
  const toggle = (rowId, field) => {
    const id = `${rowId}:${field}`;
    if (revealed.has(id)) {
      setRevealed((current) => {
        const next = new Set(current);
        next.delete(id);
        return next;
      });
      setRevealedValues((current) => {
        const next = { ...current };
        delete next[id];
        return next;
      });
      return;
    }
    setConfirmSecret({ id, rowId, field });
    setConfirmPassword("");
    setConfirmError("");
  };

  const closeConfirm = () => {
    if (confirmBusy) return;
    setConfirmSecret(null);
    setConfirmPassword("");
    setConfirmError("");
  };

  useEffect(() => {
    if (!confirmSecret) return undefined;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const handleKeyDown = (event) => {
      if (event.key === "Escape" && !confirmBusy) closeConfirm();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [confirmSecret, confirmBusy]);

  const revealSecret = async (event) => {
    event.preventDefault();
    if (!confirmSecret) return;
    setConfirmBusy(true);
    setConfirmError("");
    try {
      const result = await api("/api/dashboard/requests/reveal/", {
        method: "POST",
        body: JSON.stringify({
          request_id: confirmSecret.rowId,
          field: confirmSecret.field,
          password: confirmPassword,
        }),
      });
      setRevealed((current) => new Set(current).add(confirmSecret.id));
      setRevealedValues((current) => ({
        ...current,
        [confirmSecret.id]: result.value,
      }));
      setConfirmSecret(null);
      setConfirmPassword("");
    } catch (requestError) {
      setConfirmError(
        requestError.data?.error || tr("Неверный пароль аккаунта."),
      );
    } finally {
      setConfirmBusy(false);
    }
  };
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
          <select value={platform} onChange={(e) => setPlatform(e.target.value)} aria-label={tr("Платформа")}>
            <option value="">{tr("Все платформы")}</option>
            {(data?.filters?.platforms || []).map((value) => <option value={value} key={value}>{value}</option>)}
          </select>
          <select value={company} onChange={(e) => setCompany(e.target.value)} aria-label={tr("Предприятие")}>
            <option value="">{tr("Все предприятия")}</option>
            {(data?.filters?.companies || []).map((value) => <option value={value} key={value}>{value}</option>)}
          </select>
          <select value={position} onChange={(e) => setPosition(e.target.value)} aria-label={tr("Должность")}>
            <option value="">{tr("Все должности")}</option>
            {(data?.filters?.positions || []).map((value) => <option value={value} key={value}>{value}</option>)}
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
                        {revealed.has(id)
                          ? revealedValues[id]
                          : row[`${key}_masked`]}
                      </b>
                      <button onClick={() => toggle(row.id, key)}>
                        {tr(revealed.has(id) ? "Скрыть" : "Показать")}
                      </button>
                    </div>
                  );
                })}
              </div>
              <NavLink
                className="primary-button"
                to={`/requests/${row.id}/edit${searchParams.toString() ? `?return=${encodeURIComponent(searchParams.toString())}` : ""}`}
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
      {confirmSecret && (
        <div
          className="secret-modal-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) closeConfirm();
          }}
        >
          <form
            className="secret-modal"
            onSubmit={revealSecret}
            role="dialog"
            aria-modal="true"
            aria-labelledby="secret-modal-title"
          >
            <button
              className="secret-modal-close"
              type="button"
              onClick={closeConfirm}
              aria-label={tr("Закрыть")}
            >
              ×
            </button>
            <div className="secret-modal-icon">🔐</div>
            <h3 id="secret-modal-title">{tr("Подтверждение доступа")}</h3>
            <p>
              {tr(
                "Введите пароль вашего аккаунта, чтобы показать персональные данные.",
              )}
            </p>
            <label>
              {tr("Пароль аккаунта")}
              <input
                type="password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                autoComplete="current-password"
                autoFocus
                required
              />
            </label>
            <div className="secret-modal-error" role="alert">
              {confirmError}
            </div>
            <div className="secret-modal-actions">
              <button type="button" onClick={closeConfirm}>
                {tr("Отмена")}
              </button>
              <button
                type="submit"
                className="primary-button"
                disabled={confirmBusy}
              >
                {tr(confirmBusy ? "Проверка…" : "Подтвердить")}
              </button>
            </div>
          </form>
        </div>
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
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const returnFilters = searchParams.get("return") || "";
  const returnPath = `/requests${returnFilters ? `?${returnFilters}` : ""}`;
  const editorUrl = `/${language || "ru"}/requests/${id}/edit/?return_to=${encodeURIComponent(`/app/requests/${returnFilters ? `?${returnFilters}` : ""}`)}`;
  useEffect(() => {
    const handleEmbeddedNavigation = (event) => {
      if (event.origin !== window.location.origin || event.data?.type !== "mtu:navigate") return;
      const path = String(event.data.path || "");
      if (path === "/requests" || path.startsWith("/requests?")) navigate(path);
    };
    window.addEventListener("message", handleEmbeddedNavigation);
    return () => window.removeEventListener("message", handleEmbeddedNavigation);
  }, [navigate]);
  const handleEditorLoad = (event) => {
    syncEmbeddedTheme(event);
    try {
      const path = event.currentTarget.contentWindow.location.pathname;
      if (/^\/app\/requests\/?$/.test(path) || /^\/(ru|uz|uz-cyrl|en)\/requests\/?$/.test(path)) {
        navigate(returnPath, { replace: true });
      }
    } catch (_) {
      /* same-origin frame may still be loading */
    }
  };
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
        src={embeddedUrl(editorUrl)}
        onLoad={handleEditorLoad}
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
