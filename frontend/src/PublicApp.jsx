"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  ArrowRight,
  Bot,
  Building2,
  CheckCircle2,
  Eye,
  EyeOff,
  Languages,
  LockKeyhole,
  Moon,
  RefreshCw,
  Send,
  Sparkles,
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
    if (data?.site?.favicon_url) {
      let icon = document.querySelector("link[rel='icon']");
      if (!icon) {
        icon = document.createElement("link");
        icon.rel = "icon";
        document.head.appendChild(icon);
      }
      icon.href = data.site.favicon_url;
    }
  }, [language, data?.site?.favicon_url]);
  return (
    <div
      className="public-react-shell"
      onPointerMove={(event) => {
        if (event.pointerType === "touch") return;
        const rect = event.currentTarget.getBoundingClientRect();
        event.currentTarget.style.setProperty("--route-shift-x", `${((event.clientX - rect.left) / rect.width - .5) * 12}px`);
        event.currentTarget.style.setProperty("--route-shift-y", `${((event.clientY - rect.top) / Math.max(rect.height, 1) - .5) * 9}px`);
      }}
      onPointerLeave={(event) => {
        event.currentTarget.style.setProperty("--route-shift-x", "0px");
        event.currentTarget.style.setProperty("--route-shift-y", "0px");
      }}
    >
      <div className="public-railway-background">
        <div className="railway-aurora" aria-hidden="true"><i /><i /><i /></div>
        <div className="railway-particles" aria-hidden="true">
          {Array.from({ length: 18 }, (_, index) => <i key={index} style={{ "--particle-left": `${(index * 47) % 97}%`, "--particle-duration": `${16 + (index % 6) * 2}s`, "--particle-delay": `${index * -1.7}s` }} />)}
        </div>
        <div className="railway-light-sweep" aria-hidden="true" />
        <svg viewBox="0 0 1600 980" preserveAspectRatio="xMidYMid slice" aria-label="Railway network map">
          <defs>
            <radialGradient id="routeGlow">
              <stop offset="0" stopColor="#70ead5" stopOpacity=".95" />
              <stop offset="1" stopColor="#2ba8b5" stopOpacity="0" />
            </radialGradient>
            <filter id="softGlow" x="-200%" y="-200%" width="400%" height="400%">
              <feGaussianBlur stdDeviation="5" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>
          <path className="uzbekistan-map" d="M270 475 L335 425 445 408 515 365 600 382 665 345 770 372 842 335 935 365 1010 330 1080 352 1135 410 1225 420 1290 468 1260 525 1168 520 1110 565 1015 550 945 590 850 570 770 610 688 575 590 600 525 555 430 565 355 525 295 530 Z" />
          <path className="rail-line rail-line-halo" d="M-80 735 C180 610 235 300 520 335 S825 720 1075 560 1320 205 1690 310" />
          <path className="rail-line rail-line-main" d="M-80 735 C180 610 235 300 520 335 S825 720 1075 560 1320 205 1690 310" />
          <path className="rail-line rail-line-secondary" d="M70 160 C330 250 360 590 690 635 S1110 410 1195 760 1510 890 1680 790" />
          <path className="rail-line rail-line-branch" d="M520 335 C660 210 790 150 1015 170" />
          {[[-5,700],[160,600],[330,410],[520,335],[690,635],[890,650],[1075,560],[1195,760],[1370,360],[1545,300],[1015,170],[1450,835]].map(([cx, cy], index) => <circle key={index} cx={cx} cy={cy} r={index % 3 === 0 ? 7 : 5} />)}
          <g className="station-labels">
            <text x="278" y="392">TOSHKENT</text>
            <text x="645" y="670">JIZZAX</text>
            <text x="1034" y="600">SAMARQAND</text>
            <text x="1340" y="342">BUXORO</text>
          </g>
          <g className="route-codes">
            <text x="435" y="300">TAS–01</text>
            <text x="775" y="688">JIZ–02</text>
            <text x="1120" y="525">SAM–03</text>
            <text x="1420" y="322">BUX–04</text>
          </g>
          <g className="station-pulses">
            <circle cx="330" cy="410" r="17" /><circle cx="690" cy="635" r="17" />
            <circle cx="1075" cy="560" r="17" /><circle cx="1370" cy="360" r="17" />
          </g>
          <g className="interactive-stations">
            <g tabIndex="0" aria-label="Toshkent — markaziy temir yo‘l uzeli"><circle cx="330" cy="410" r="13" /><title>Toshkent · Markaziy temir yo‘l uzeli</title></g>
            <g tabIndex="0" aria-label="Jizzax — regional temir yo‘l uzeli"><circle cx="690" cy="635" r="13" /><title>Jizzax · Regional temir yo‘l uzeli</title></g>
            <g tabIndex="0" aria-label="Samarqand — regional temir yo‘l uzeli"><circle cx="1075" cy="560" r="13" /><title>Samarqand · Regional temir yo‘l uzeli</title></g>
            <g tabIndex="0" aria-label="Buxoro — regional temir yo‘l uzeli"><circle cx="1370" cy="360" r="13" /><title>Buxoro · Regional temir yo‘l uzeli</title></g>
          </g>
          <g className="route-pulse" transform="translate(520 335)">
            <circle r="17" fill="url(#routeGlow)" />
            <circle r="5" filter="url(#softGlow)" />
            <animateMotion dur="18s" repeatCount="indefinite" path="M0 0 C305 385 555 225 800 -130 S1080 -80 1170 -25" />
          </g>
          <g className="railway-train">
            <rect x="-16" y="-8" width="26" height="14" rx="4" />
            <path d="M10-5h7l7 7v4H10z" />
            <circle cx="-8" cy="9" r="3" /><circle cx="15" cy="9" r="3" />
            <path className="train-light" d="M24 1l13-5v10z" />
            <animateMotion dur="34s" repeatCount="indefinite" rotate="auto" path="M-80 735 C180 610 235 300 520 335 S825 720 1075 560 1320 205 1690 310" />
          </g>
        </svg>
      </div>
      <header className="public-react-header">
        <a
          className="public-react-brand"
          href={`/app/public/?lang=${language}`}
        >
          <img
            src={data?.site?.logo_url || "/static/img/mtu-forum-mark.svg"}
            alt={data?.site?.name || "MTU FORUM"}
            onError={(event) => {
              event.currentTarget.onerror = null;
              event.currentTarget.src = "/static/img/mtu-forum-mark.svg";
            }}
          />
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

function SearchableSelect({ name, label, items, value, onChange, placeholder, errors }) {
  const selected = items.find((item) => item.value && String(item.value) === String(value));
  const [query, setQuery] = useState(selected?.label || "");
  const [open, setOpen] = useState(false);
  useEffect(() => setQuery(selected?.label || ""), [selected?.label]);
  const filtered = items
    .filter((item) => item.value && item.label.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 12);
  return (
    <label className="searchable-select">
      <span>{label}</span>
      <input
        name={name}
        value={query}
        placeholder={placeholder}
        autoComplete="off"
        onFocus={() => setOpen(true)}
        onChange={(event) => {
          setQuery(event.target.value);
          onChange(name, "");
          setOpen(true);
        }}
        onBlur={() => setTimeout(() => setOpen(false), 120)}
      />
      {open && (
        <div className="searchable-options">
          {filtered.length ? filtered.map((item) => (
            <button key={`${name}-${item.value}`} type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => {
              onChange(name, item.value);
              setQuery(item.label);
              setOpen(false);
            }}>
              {item.label}
            </button>
          )) : <small>{placeholder}</small>}
        </div>
      )}
      <FieldError errors={errors} name={name} />
    </label>
  );
}

function PublicFormAssistant({ language, values, labels, success }) {
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState(() => {
    if (typeof window === "undefined") return null;
    try {
      const saved = JSON.parse(window.localStorage.getItem("public-ai-position"));
      return Number.isFinite(saved?.x) && Number.isFinite(saved?.y) ? saved : null;
    } catch { return null; }
  });
  const dragState = useRef(null);
  const moved = useRef(false);
  const positionRef = useRef(position);
  const assistantCopy = {
    ru: { title: "AI-помощник", intro: "Помогу заполнить заявку без ошибок.", progress: "Заполнено", next: "Следующее поле", focus: "Перейти к полю", check: "Проверить форму", ready: "Все поля заполнены. Проверьте данные и отправьте заявку.", sent: "Заявка успешно отправлена. Спасибо!", tips: { platform: "Выберите нужную корпоративную платформу из списка.", full_name: "Введите фамилию, имя и отчество полностью.", pnfl: "ПИНФЛ должен содержать ровно 14 цифр.", passport: "Введите 2 латинские буквы и 7 цифр, например AB1234567.", company: "Выберите предприятие из предложенного списка.", position: "Выберите вашу должность из списка.", phone: "Введите номер Узбекистана в формате +998-XX-XXX-XX-XX.", cause: "Кратко и понятно опишите причину получения доступа." } },
    uz: { title: "AI yordamchi", intro: "Arizani xatosiz to'ldirishga yordam beraman.", progress: "To'ldirildi", next: "Keyingi maydon", focus: "Maydonga o'tish", check: "Formani tekshirish", ready: "Barcha maydonlar to'ldirildi. Ma'lumotlarni tekshirib, arizani yuboring.", sent: "Ariza muvaffaqiyatli yuborildi. Rahmat!", tips: { platform: "Kerakli korporativ platformani ro'yxatdan tanlang.", full_name: "Familiya, ism va otangiz ismini to'liq kiriting.", pnfl: "JSHSHIR aynan 14 ta raqamdan iborat bo'lishi kerak.", passport: "2 ta lotin harfi va 7 ta raqam kiriting, masalan AB1234567.", company: "Korxonani taklif qilingan ro'yxatdan tanlang.", position: "Lavozimingizni ro'yxatdan tanlang.", phone: "O'zbekiston raqamini +998-XX-XXX-XX-XX formatida kiriting.", cause: "Kirish olish sababini qisqa va aniq yozing." } },
    "uz-cyrl": { title: "AI ёрдамчи", intro: "Аризани хатосиз тўлдиришга ёрдам бераман.", progress: "Тўлдирилди", next: "Кейинги майдон", focus: "Майдонга ўтиш", check: "Формани текшириш", ready: "Барча майдонлар тўлдирилди. Маълумотларни текшириб, аризани юборинг.", sent: "Ариза муваффақиятли юборилди. Раҳмат!", tips: { platform: "Керакли корпоратив платформани рўйхатдан танланг.", full_name: "Фамилия, исм ва отангиз исмини тўлиқ киритинг.", pnfl: "ЖШШИР айнан 14 та рақамдан иборат бўлиши керак.", passport: "2 та лотин ҳарфи ва 7 та рақам киритинг, масалан AB1234567.", company: "Корхонани таклиф қилинган рўйхатдан танланг.", position: "Лавозимингизни рўйхатдан танланг.", phone: "Ўзбекистон рақамини +998-XX-XXX-XX-XX форматида киритинг.", cause: "Кириш олиш сабабини қисқа ва аниқ ёзинг." } },
    en: { title: "AI assistant", intro: "I will help you complete the request without errors.", progress: "Completed", next: "Next field", focus: "Go to field", check: "Check form", ready: "All fields are complete. Review the details and submit the request.", sent: "The request was submitted successfully. Thank you!", tips: { platform: "Select the required corporate platform from the list.", full_name: "Enter your full surname, first name, and patronymic.", pnfl: "PINFL must contain exactly 14 digits.", passport: "Enter 2 Latin letters and 7 digits, for example AB1234567.", company: "Select your company from the suggested list.", position: "Select your position from the list.", phone: "Enter an Uzbekistan number in +998-XX-XXX-XX-XX format.", cause: "Briefly describe why you need access." } },
  }[language];
  const fields = [
    ["platform", labels.platform, Boolean(values.platform)],
    ["full_name", labels.full_name, values.full_name.trim().length >= 5],
    ["pnfl", labels.pnfl, /^\d{14}$/.test(values.pnfl)],
    ["passport", labels.passport, /^[A-Za-z]{2}\d{7}$/.test(values.passport.replace(/\s/g, ""))],
    ["company", labels.company, Boolean(values.company)],
    ["position", labels.position, Boolean(values.position)],
    ["phone", labels.phone, /^998\d{9}$/.test(values.phone.replace(/\D/g, ""))],
    ["cause", labels.cause, values.cause.trim().length >= 3],
  ];
  const completed = fields.filter((field) => field[2]).length;
  const nextField = fields.find((field) => !field[2]);
  const clampPosition = useCallback((x, y) => {
    const viewport = window.visualViewport;
    const viewportWidth = Math.min(window.innerWidth, document.documentElement.clientWidth, viewport?.width || Infinity);
    const viewportHeight = Math.min(window.innerHeight, document.documentElement.clientHeight, viewport?.height || Infinity);
    const assistantWidth = Math.min(305, viewportWidth - 16);
    const panelHeight = open ? (document.querySelector(".public-ai-panel")?.getBoundingClientRect().height || 190) + 64 : 54;
    return {
      x: Math.max(8, Math.min(x, viewportWidth - assistantWidth - 8)),
      y: Math.max(8, Math.min(y, viewportHeight - panelHeight - 8)),
    };
  }, [open]);
  const startDrag = (event) => {
    if (event.button !== 0) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const origin = position || { x: rect.left, y: rect.top };
    dragState.current = { pointerId: event.pointerId, startX: event.clientX, startY: event.clientY, origin };
    moved.current = false;
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const moveAssistant = (event) => {
    const drag = dragState.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    const dx = event.clientX - drag.startX;
    const dy = event.clientY - drag.startY;
    if (Math.hypot(dx, dy) < 4 && !moved.current) return;
    moved.current = true;
    const next = clampPosition(drag.origin.x + dx, drag.origin.y + dy);
    positionRef.current = next;
    setPosition(next);
  };
  const finishDrag = (event) => {
    if (!dragState.current || dragState.current.pointerId !== event.pointerId) return;
    dragState.current = null;
    if (moved.current && positionRef.current) {
      window.localStorage.setItem("public-ai-position", JSON.stringify(positionRef.current));
    }
  };
  useEffect(() => {
    const keepOnScreen = () => {
      if (!positionRef.current) return;
      const next = clampPosition(positionRef.current.x, positionRef.current.y);
      positionRef.current = next;
      setPosition(next);
    };
    window.addEventListener("resize", keepOnScreen);
    window.visualViewport?.addEventListener("resize", keepOnScreen);
    keepOnScreen();
    return () => {
      window.removeEventListener("resize", keepOnScreen);
      window.visualViewport?.removeEventListener("resize", keepOnScreen);
    };
  }, [clampPosition]);
  const focusNext = () => {
    if (!nextField) return;
    const input = document.querySelector(`[name="${nextField[0]}"]`);
    input?.focus();
    input?.scrollIntoView({ behavior: "smooth", block: "center" });
    input?.classList.add("ai-field-focus");
    window.setTimeout(() => input?.classList.remove("ai-field-focus"), 1800);
  };
  const assistant = (
    <aside className={`public-form-assistant${open ? " is-open" : ""}${position ? " is-dragged" : ""}`} style={position ? { left: position.x, top: position.y } : undefined}>
      <button className="public-ai-trigger" type="button" onPointerDown={startDrag} onPointerMove={moveAssistant} onPointerUp={finishDrag} onPointerCancel={finishDrag} onClick={() => {
        if (moved.current) { moved.current = false; return; }
        setOpen((value) => !value);
      }} aria-label={assistantCopy.title} aria-expanded={open}>
        <span><Bot /></span><i />
      </button>
      <div className="public-ai-hint">{success ? assistantCopy.sent : nextField ? `${assistantCopy.next}: ${nextField[1]}` : assistantCopy.ready}</div>
      {open && (
        <div className="public-ai-panel">
          <header><span><Sparkles /></span><div><b>{assistantCopy.title}</b><small>{assistantCopy.intro}</small></div></header>
          <div className="public-ai-progress"><span><i style={{ width: `${(completed / fields.length) * 100}%` }} /></span><b>{assistantCopy.progress}: {completed}/{fields.length}</b></div>
          <p>{success ? assistantCopy.sent : nextField ? assistantCopy.tips[nextField[0]] : assistantCopy.ready}</p>
          {!success && nextField && <button type="button" onClick={focusNext}>{assistantCopy.focus}<ArrowRight /></button>}
          {!success && !nextField && <button type="button" onClick={() => document.querySelector(".request-form .public-submit")?.focus()}>{assistantCopy.check}<CheckCircle2 /></button>}
        </div>
      )}
    </aside>
  );
  return typeof document === "undefined" ? assistant : createPortal(assistant, document.body);
}

function PublicRequest({ data }) {
  const tr = createTranslator(data.language);
  const [publicStats, setPublicStats] = useState(data.public_stats || {});
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
  const [success, setSuccess] = useState(null);
  const refreshPublicStats = useCallback(() => {
    return api(`/api/react/public/?lang=${encodeURIComponent(data.language)}&_=${Date.now()}`)
      .then((result) => setPublicStats(result.public_stats || {}))
      .catch(() => { /* Keep the last confirmed values if the connection is temporarily unavailable. */ });
  }, [data.language]);
  useEffect(() => {
    const statsTimer = window.setInterval(refreshPublicStats, 30000);
    return () => window.clearInterval(statsTimer);
  }, [refreshPublicStats]);
  const change = (e) =>
    setValues((v) => ({ ...v, [e.target.name]: e.target.value }));
  const changePnfl = (e) => {
    const pnfl = e.target.value.replace(/\D/g, "").slice(0, 14);
    setValues((current) => ({ ...current, pnfl }));
  };
  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setErrors({});
    setSuccess(null);
    try {
      const result = await api("/api/react/public/", {
        method: "POST",
        body: JSON.stringify({ ...values, lang: data.language }),
      });
      setSuccess(result);
      await refreshPublicStats();
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
  const copy = {
    ru: { steps: ["Данные", "Проверка", "Готово"], searchPlatform: "Найти платформу…", searchCompany: "Найти предприятие…", searchPosition: "Найти должность…", sent: "Заявка отправлена", number: "Номер заявки", next: "Мы передали данные ответственному сотруднику.", another: "Подать ещё одну заявку", online: "Все системы работают", today: "Заявок сегодня", done: "Обработано", average: "Среднее время", minutes: "мин.", hours: "ч.", days: "дн." },
    uz: { steps: ["Ma’lumotlar", "Tekshirish", "Tayyor"], searchPlatform: "Platformani qidiring…", searchCompany: "Korxonani qidiring…", searchPosition: "Lavozimni qidiring…", sent: "Ariza yuborildi", number: "Ariza raqami", next: "Ma’lumotlar mas’ul xodimga yuborildi.", another: "Yana ariza yuborish", online: "Barcha tizimlar ishlamoqda", today: "Bugungi arizalar", done: "Bajarildi", average: "O‘rtacha vaqt", minutes: "daq.", hours: "soat", days: "kun" },
    "uz-cyrl": { steps: ["Маълумотлар", "Текшириш", "Тайёр"], searchPlatform: "Платформани қидиринг…", searchCompany: "Корхонани қидиринг…", searchPosition: "Лавозимни қидиринг…", sent: "Ариза юборилди", number: "Ариза рақами", next: "Маълумотлар масъул ходимга юборилди.", another: "Яна ариза юбориш", online: "Барча тизимлар ишламоқда", today: "Бугунги аризалар", done: "Бажарилди", average: "Ўртача вақт", minutes: "дақ.", hours: "соат", days: "кун" },
    en: { steps: ["Details", "Review", "Done"], searchPlatform: "Search platform…", searchCompany: "Search company…", searchPosition: "Search position…", sent: "Request submitted", number: "Request number", next: "The details were sent to the responsible employee.", another: "Submit another request", online: "All systems operational", today: "Requests today", done: "Completed", average: "Average time", minutes: "min", hours: "hr", days: "d" },
  }[data.language] || null;
  const requiredReady = values.platform && values.full_name && /^[0-9]{14}$/.test(values.pnfl) && values.passport && values.company && values.position && values.phone && values.cause;
  const activeStep = success ? 3 : requiredReady ? 2 : 1;
  const formatDuration = (minutes) => {
    if (minutes == null) return "—";
    if (minutes < 60) return `${minutes} ${copy.minutes}`;
    if (minutes < 1440) return `${Math.floor(minutes / 60)} ${copy.hours} ${minutes % 60} ${copy.minutes}`;
    return `${Math.floor(minutes / 1440)} ${copy.days} ${Math.floor((minutes % 1440) / 60)} ${copy.hours}`;
  };
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
          <div className="public-live-status"><i />{copy.online}<small>{publicStats.active_services || 0} WEB</small></div>
          <div className="public-quick-stats">
            <div><strong>{publicStats.requests_today || 0}</strong><span>{copy.today}</span></div>
            <div><strong>{publicStats.completed_today || 0}</strong><span>{copy.done}</span></div>
            <div><strong>{formatDuration(publicStats.average_processing_minutes)}</strong><span>{copy.average}</span></div>
          </div>
        </section>
        <form className="public-react-card request-form" onSubmit={submit}>
          <PublicFormAssistant language={data.language} values={values} labels={data.texts} success={success} />
          <div className="public-card-title">
            <span>
              <Send />
            </span>
            <div>
              <small>{tr("НОВАЯ ЗАЯВКА")}</small>
              <h2>{tr("Данные сотрудника")}</h2>
            </div>
          </div>
          <div className="request-progress" aria-label={copy.steps.join(", ")}>
            {copy.steps.map((step, index) => (
              <div key={step} className={activeStep >= index + 1 ? "active" : ""}>
                <i>{activeStep > index + 1 ? <CheckCircle2 /> : index + 1}</i>
                <span>{step}</span>
              </div>
            ))}
          </div>
          {success ? (
            <div className="request-success-screen">
              <span><CheckCircle2 /></span>
              <small>{copy.sent}</small>
              <h2>{copy.number} <b>#{success.request_id}</b></h2>
              <p>{success.message}</p>
              <p>{copy.next}</p>
              <button type="button" className="public-submit" onClick={() => setSuccess(null)}>{copy.another}<ArrowRight /></button>
            </div>
          ) : <>
          <FieldError errors={errors} name="__all__" />
          <div className="public-form-grid">
            <SearchableSelect name="platform" label={data.texts.platform} items={data.choices.platforms} value={values.platform} onChange={(name, value) => setValues((current) => ({ ...current, [name]: value }))} placeholder={copy.searchPlatform} errors={errors} />
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
                onChange={changePnfl}
                inputMode="numeric"
                minLength={14}
                maxLength={14}
                pattern="[0-9]{14}"
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
            <SearchableSelect name="company" label={data.texts.company} items={data.choices.companies} value={values.company} onChange={(name, value) => setValues((current) => ({ ...current, [name]: value }))} placeholder={copy.searchCompany} errors={errors} />
            <SearchableSelect name="position" label={data.texts.position} items={data.choices.positions} value={values.position} onChange={(name, value) => setValues((current) => ({ ...current, [name]: value }))} placeholder={copy.searchPosition} errors={errors} />
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
          </>}
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
      const loginLocked = err.data?.error_code === "login_locked";
      setError(
        loginLocked
          ? tr("Слишком много ошибок входа. Повторите через 15 минут.")
          : captchaFailed
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
