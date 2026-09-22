"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  Building2,
  CheckCircle2,
  Eye,
  EyeOff,
  Languages,
  LockKeyhole,
  Moon,
  RefreshCw,
  Send,
  Sun,
  Sunrise,
  UserRound,
} from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { api } from "./api";
import { createTranslator } from "./i18n";
import { useSolarTheme } from "./useSolarTheme";
import { VersionSwitch } from "./VersionSwitch";
import { AccessibilityControl } from "./AccessibilityControl";

const languageLabels = { ru: "RU", uz: "UZ", "uz-cyrl": "ЎЗ", en: "EN" };

function PublicTools({ language, legacyUrl }) {
  const tr = createTranslator(language);
  const {
    mode: themeMode,
    theme,
    cycle: cycleTheme,
    loading: solarLoading,
    details: solarDetails,
  } = useSolarTheme(language);
  const [accessOpen, setAccessOpen] = useState(false);
  const [languages, setLanguages] = useState(false);
  const themeTitle =
    themeMode === "auto"
      ? `${tr("Авто: восход и закат")}${solarDetails ? ` — ${solarDetails}` : solarLoading ? ` — ${tr("Получение времени…")}` : ""}`
      : themeMode === "system"
        ? tr("Как в системе")
        : tr("Противоположно системе");
  return (
    <div className="public-tools">
      <VersionSwitch
        legacyUrl={legacyUrl}
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
        language={language}
        open={accessOpen}
        onOpenChange={(nextOpen) => {
          setAccessOpen(nextOpen);
          if (nextOpen) setLanguages(false);
        }}
      />
      <div className="tool-menu">
        <button
          className="icon-button language-button"
          onClick={() => {
            setLanguages(!languages);
            setAccessOpen(false);
          }}
          aria-label={tr("Выбрать язык")}
        >
          <Languages />
          <span>{languageLabels[language] || "RU"}</span>
        </button>
        {languages && (
          <nav className="react-popover language-popover public-language-popover">
            {Object.entries(languageLabels).map(([code, label]) => (
              <a key={code} href={`?lang=${code}`}>
                {label}
                <span>
                  {code === "ru"
                    ? "Русский"
                    : code === "en"
                      ? "English"
                      : code === "uz"
                        ? "O‘zbekcha"
                        : "Ўзбекча"}
                </span>
              </a>
            ))}
          </nav>
        )}
      </div>
    </div>
  );
}

function PublicFrame({ data, children, page }) {
  const language = data?.language || "ru";
  const tr = createTranslator(language);
  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);
  return (
    <div className="public-react-shell">
      <header className="public-react-header">
        <a
          className="public-react-brand"
          href={`/app/public/?lang=${language}`}
        >
          <img src="/static/img/mtu-forum-mark.svg" />
          <strong>{data?.site?.name || "MTU FORUM"}</strong>
        </a>
        <PublicTools
          language={language}
          legacyUrl={
            page === "login"
              ? data?.links?.legacy_login
              : data?.links?.legacy_public
          }
        />
        <a
          className="public-header-action"
          href={
            page === "login"
              ? `/app/public/?lang=${language}`
              : `/app/login/?lang=${language}`
          }
        >
          {tr(page === "login" ? "Подать заявку" : "Войти")}
          <ArrowRight />
        </a>
      </header>
      {children}
    </div>
  );
}

function usePublicData(language) {
  const [state, setState] = useState({ loading: true, data: null, error: "" });
  useEffect(() => {
    let active = true;
    setState({ loading: true, data: null, error: "" });
    api(`/api/react/public/?lang=${encodeURIComponent(language)}`)
      .then((data) => active && setState({ loading: false, data, error: "" }))
      .catch(
        (error) =>
          active &&
          setState({ loading: false, data: null, error: error.message }),
      );
    return () => {
      active = false;
    };
  }, [language]);
  return state;
}

function FieldError({ errors, name }) {
  const text = errors?.[name]?.[0]?.message;
  return text ? <small className="field-error">{text}</small> : null;
}

function PublicRequest({ data }) {
  const tr = createTranslator(data.language);
  const [values, setValues] = useState({
    platform: "",
    full_name: "",
    pnfl: "",
    passport: "",
    company: "",
    position: "",
    phone: "",
    cause: "",
  });
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);
  const [success, setSuccess] = useState("");
  const change = (e) =>
    setValues((v) => ({ ...v, [e.target.name]: e.target.value }));
  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setErrors({});
    setSuccess("");
    try {
      const result = await api("/api/react/public/", {
        method: "POST",
        body: JSON.stringify({ ...values, lang: data.language }),
      });
      setSuccess(result.message);
      setValues({
        platform: "",
        full_name: "",
        pnfl: "",
        passport: "",
        company: "",
        position: "",
        phone: "",
        cause: "",
      });
    } catch (error) {
      setErrors(
        error.data?.errors || { __all__: [{ message: error.message }] },
      );
    } finally {
      setBusy(false);
    }
  };
  const select = (name, label, items) => (
    <label>
      <span>{label}</span>
      <select name={name} value={values[name]} onChange={change}>
        {items.map((item) => (
          <option key={`${name}-${item.value}`} value={item.value}>
            {item.label}
          </option>
        ))}
      </select>
      <FieldError errors={errors} name={name} />
    </label>
  );
  return (
    <PublicFrame data={data} page="public">
      <main className="public-react-main">
        <section className="public-react-copy">
          <span className="public-kicker">
            {tr("КОРПОРАТИВНАЯ ЖЕЛЕЗНОДОРОЖНАЯ ПЛАТФОРМА")}
          </span>
          <h1>{tr("Подать заявку на доступ")}</h1>
          <p>
            {tr(
              "Единое цифровое окно для подключения к корпоративным сервисам MTU FORUM.",
            )}
          </p>
          <div className="public-benefits">
            <div>
              <CheckCircle2 />
              <span>
                <b>{tr("Быстрая обработка")}</b>
                <small>
                  {tr("Заявка сразу поступает ответственному сотруднику")}
                </small>
              </span>
            </div>
            <div>
              <LockKeyhole />
              <span>
                <b>{tr("Безопасные данные")}</b>
                <small>{tr("Проверка выполняется средствами Django")}</small>
              </span>
            </div>
          </div>
        </section>
        <form className="public-react-card request-form" onSubmit={submit}>
          <div className="public-card-title">
            <span>
              <Send />
            </span>
            <div>
              <small>{tr("НОВАЯ ЗАЯВКА")}</small>
              <h2>{tr("Данные сотрудника")}</h2>
            </div>
          </div>
          {success && (
            <div className="public-success">
              <CheckCircle2 />
              {success}
            </div>
          )}
          <FieldError errors={errors} name="__all__" />
          <div className="public-form-grid">
            {select("platform", data.texts.platform, data.choices.platforms)}
            <label>
              <span>{data.texts.full_name}</span>
              <input
                name="full_name"
                value={values.full_name}
                onChange={change}
                placeholder={data.texts.full_name_placeholder}
              />
              <FieldError errors={errors} name="full_name" />
            </label>
            <label>
              <span>{data.texts.pnfl}</span>
              <input
                name="pnfl"
                value={values.pnfl}
                onChange={change}
                inputMode="numeric"
                placeholder={data.texts.pnfl_placeholder}
              />
              <FieldError errors={errors} name="pnfl" />
            </label>
            <label>
              <span>{data.texts.passport}</span>
              <input
                name="passport"
                value={values.passport}
                onChange={change}
                placeholder="AB1234567"
              />
              <FieldError errors={errors} name="passport" />
            </label>
            {select("company", data.texts.company, data.choices.companies)}
            {select("position", data.texts.position, data.choices.positions)}
            <label>
              <span>{data.texts.phone}</span>
              <input
                name="phone"
                value={values.phone}
                onChange={change}
                placeholder="+998-XX-XXX-XX-XX"
              />
              <FieldError errors={errors} name="phone" />
            </label>
            <label className="wide">
              <span>{data.texts.cause}</span>
              <textarea
                name="cause"
                value={values.cause}
                onChange={change}
                rows="3"
                placeholder={data.texts.cause_placeholder}
              />
              <FieldError errors={errors} name="cause" />
            </label>
          </div>
          <button
            className="public-submit"
            disabled={busy}
          >
            {tr(busy ? "Отправка…" : "Отправить заявку")}
            <ArrowRight />
          </button>
        </form>
      </main>
      {data.web_platforms.length > 0 && (
        <section className="public-services">
          <span>{tr("ДОСТУПНЫЕ WEB-ПЛАТФОРМЫ")}</span>
          <div>
            {data.web_platforms.map((item) => (
              <a
                key={item.id}
                href={item.url || "#"}
                target={item.url ? "_blank" : undefined}
                rel="noreferrer"
              >
                <span>
                  {item.image_url ? (
                    <img src={item.image_url} />
                  ) : (
                    <Building2 />
                  )}
                </span>
                <b>{item.name}</b>
              </a>
            ))}
          </div>
        </section>
      )}
    </PublicFrame>
  );
}

function Login({ data }) {
  const tr = useMemo(() => createTranslator(data.language), [data.language]);
  const [values, setValues] = useState({
    username: "",
    password: "",
    remember_me: false,
    captcha_answer: "",
  });
  const [captcha, setCaptcha] = useState({ question: "", loading: true });
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [resetBusy, setResetBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const navigate = useNavigate();
  const loadCaptcha = useCallback(async () => {
    setCaptcha((current) => ({ ...current, loading: true }));
    try {
      const challenge = await api("/api/react/captcha/");
      setCaptcha({ question: challenge.question, loading: false });
    } catch {
      setCaptcha({ question: "", loading: false });
      setError(tr("Не удалось загрузить проверку. Обновите её."));
    }
  }, [tr]);
  useEffect(() => {
    loadCaptcha();
  }, [loadCaptcha]);
  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const result = await api("/api/react/login/", {
        method: "POST",
        body: JSON.stringify(values),
      });
      window.location.assign(result.redirect || "/app/");
    } catch (err) {
      const captchaFailed = err.data?.error_code === "captcha_invalid";
      setError(
        captchaFailed
          ? tr("Неверный ответ. Решите новый пример.")
          : err.data?.errors?.__all__?.[0]?.message ||
              tr("Неверный логин или пароль."),
      );
      if (err.data?.captcha_refresh) {
        setValues((current) => ({ ...current, captcha_answer: "" }));
        await loadCaptcha();
      }
    } finally {
      setBusy(false);
    }
  };
  const resetPassword = async () => {
    if (!values.username.trim()) {
      setError(tr("Сначала введите логин."));
      return;
    }
    setResetBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await api("/api/react/password-reset/", {
        method: "POST",
        body: JSON.stringify({ username: values.username.trim() }),
      });
      setNotice(tr("Откройте Telegram, чтобы получить новый пароль."));
      window.location.assign(result.deep_link);
    } catch (err) {
      setError(err.data?.detail || tr("Не удалось открыть восстановление через Telegram."));
    } finally {
      setResetBusy(false);
    }
  };
  return (
    <PublicFrame data={data} page="login">
      <main className="login-react-main">
        <section className="login-react-copy">
          <span className="public-kicker">{tr("НОВАЯ ВЕРСИЯ ПЛАТФОРМЫ")}</span>
          <h1>{tr("Добро пожаловать в MTU FORUM")}</h1>
          <p>
            {tr(
              "Заявки, справочники, сообщения и управление доступами — в едином рабочем пространстве.",
            )}
          </p>
          <div className="login-visual">
            <ShieldMark />
            <div>
              <b>{tr("Защищённый вход")}</b>
              <small>{tr("Сессия и права доступа управляются Django")}</small>
            </div>
          </div>
        </section>
        <form className="public-react-card login-react-card" onSubmit={submit}>
          <div className="public-card-title">
            <span>
              <UserRound />
            </span>
            <div>
              <small>{tr("АВТОРИЗАЦИЯ")}</small>
              <h2>{tr("Вход в систему")}</h2>
            </div>
          </div>
          {error && <div className="public-error">{error}</div>}
          {notice && <div className="public-notice">{notice}</div>}
          <label>
            <span>{tr("Логин")}</span>
            <div className="input-with-icon">
              <UserRound />
              <input
                name="username"
                autoComplete="username"
                value={values.username}
                onChange={(e) =>
                  setValues((v) => ({ ...v, username: e.target.value }))
                }
                placeholder={tr("Введите логин")}
                required
              />
            </div>
          </label>
          <label>
            <span>{tr("Пароль")}</span>
            <div className="input-with-icon">
              <LockKeyhole />
              <input
                name="password"
                type={show ? "text" : "password"}
                autoComplete="current-password"
                value={values.password}
                onChange={(e) =>
                  setValues((v) => ({ ...v, password: e.target.value }))
                }
                placeholder={tr("Введите пароль")}
                required
              />
              <button
                type="button"
                onClick={() => setShow(!show)}
                aria-label={tr(show ? "Скрыть пароль" : "Показать пароль")}
              >
                {show ? <EyeOff /> : <Eye />}
              </button>
            </div>
          </label>
          <label className="remember-line">
            <input
              type="checkbox"
              checked={values.remember_me}
              onChange={(e) =>
                setValues((v) => ({ ...v, remember_me: e.target.checked }))
              }
            />{" "}
            {tr("Запомнить меня")}
          </label>
          <section className="human-check" aria-label={tr("Проверка человека")}>
            <div className="human-check-copy">
              <strong>{tr("Проверка человека")}</strong>
              <small>{tr("Решите математический пример")}</small>
            </div>
            <div className="human-check-row">
              <output aria-live="polite">
                {captcha.loading ? "…" : captcha.question || "—"}
              </output>
              <span>=</span>
              <input
                name="captcha_answer"
                inputMode="numeric"
                autoComplete="off"
                value={values.captcha_answer}
                onChange={(e) =>
                  setValues((current) => ({
                    ...current,
                    captcha_answer: e.target.value.replace(/[^0-9-]/g, ""),
                  }))
                }
                placeholder={tr("Ответ")}
                aria-label={tr("Ответ на математический пример")}
                required
              />
              <button
                type="button"
                onClick={() => {
                  setValues((current) => ({
                    ...current,
                    captcha_answer: "",
                  }));
                  loadCaptcha();
                }}
                disabled={captcha.loading}
                aria-label={tr("Обновить пример")}
                title={tr("Обновить пример")}
              >
                <RefreshCw />
              </button>
            </div>
          </section>
          <button className="public-submit" disabled={busy}>
            {tr(busy ? "Вход…" : "Войти")}
            <ArrowRight />
          </button>
          <button
            className="telegram-reset-action"
            type="button"
            onClick={resetPassword}
            disabled={resetBusy}
          >
            <Send />
            {tr(resetBusy ? "Подготовка ссылки…" : "Восстановить пароль через Telegram")}
          </button>
          <div className="sso-divider">
            <span>{tr("или")}</span>
          </div>
          <div className="sso-grid">
            <a href={data.links.oneid}>OneID</a>
            <a href={data.links.eimzo}>E-IMZO</a>
          </div>
          <button
            className="text-action"
            type="button"
            onClick={() => navigate(`/public/?lang=${data.language}`)}
          >
            {tr("Нет аккаунта? Подать заявку")}
          </button>
        </form>
      </main>
    </PublicFrame>
  );
}

function ShieldMark() {
  return (
    <div className="shield-mark">
      <LockKeyhole />
    </div>
  );
}

export default function PublicApp() {
  const location = useLocation();
  const language = useMemo(
    () => new URLSearchParams(location.search).get("lang") || "ru",
    [location.search],
  );
  const { loading, data, error } = usePublicData(language);
  const tr = createTranslator(language);
  if (loading)
    return (
      <div className="public-state">
        <span className="spinner" />
        {tr("Загрузка…")}
      </div>
    );
  if (error) return <div className="public-state error">{error}</div>;
  return location.pathname.startsWith("/login") ? (
    <Login data={data} />
  ) : (
    <PublicRequest data={data} />
  );
}
