import { useEffect, useState } from "react";
import { Accessibility, RotateCcw } from "lucide-react";
import { createTranslator } from "./i18n";

const readFlag = (key) =>
  typeof window !== "undefined" && window.localStorage.getItem(key) === "on";

const readView = () => {
  if (typeof window === "undefined") return "normal";
  const saved = window.localStorage.getItem("mtu-access-view");
  if (["normal", "whiteblack", "dark"].includes(saved)) return saved;
  return readFlag("mtu-accessibility") ? "dark" : "normal";
};

export function AccessibilityControl({ language = "ru", open, onOpenChange }) {
  const tr = createTranslator(language);
  const [view, setView] = useState(readView);
  const [fontScale, setFontScale] = useState(() =>
    typeof window === "undefined"
      ? 0
      : Number(window.localStorage.getItem("mtu-font-scale") || 0),
  );
  const [soundGuide, setSoundGuide] = useState(() =>
    readFlag("mtu-sound-guide"),
  );
  const [underline, setUnderline] = useState(() =>
    readFlag("mtu-underline-links"),
  );
  const [reduceMotion, setReduceMotion] = useState(() =>
    readFlag("mtu-reduce-motion"),
  );
  const [largeCursor, setLargeCursor] = useState(() =>
    readFlag("mtu-large-cursor"),
  );

  useEffect(() => {
    const root = document.documentElement;
    const scale = Math.max(0, Math.min(Number(fontScale) || 0, 40));
    root.style.setProperty("--react-font-scale", String(1 + scale / 100));
    root.style.setProperty("--access-page-zoom", String(1 + scale / 100));
    root.classList.toggle("accessibility-mode", view === "dark");
    root.classList.toggle("access-black-white", view === "whiteblack");
    root.classList.toggle("access-invert", view === "dark");
    root.classList.toggle("react-access-whiteblack", view === "whiteblack");
    root.classList.toggle("react-access-dark", view === "dark");
    root.classList.toggle("react-access-contrast", view === "dark");
    root.classList.toggle("sound-guide-mode", soundGuide);
    root.classList.toggle("access-underline-links", underline);
    root.classList.toggle("access-reduce-motion", reduceMotion);
    root.classList.toggle("access-large-cursor", largeCursor);
    root.classList.toggle("react-underline-links", underline);
    root.classList.toggle("react-reduce-motion", reduceMotion);
    root.classList.toggle("react-large-cursor", largeCursor);

    window.localStorage.setItem("mtu-access-view", view);
    window.localStorage.setItem(
      "mtu-accessibility",
      view === "dark" ? "on" : "off",
    );
    window.localStorage.setItem("mtu-font-scale", String(scale));
    window.localStorage.setItem("mtu-sound-guide", soundGuide ? "on" : "off");
    window.localStorage.setItem(
      "mtu-underline-links",
      underline ? "on" : "off",
    );
    window.localStorage.setItem(
      "mtu-reduce-motion",
      reduceMotion ? "on" : "off",
    );
    window.localStorage.setItem("mtu-large-cursor", largeCursor ? "on" : "off");
  }, [view, fontScale, soundGuide, underline, reduceMotion, largeCursor]);

  useEffect(() => {
    if (!soundGuide || typeof window.speechSynthesis === "undefined")
      return undefined;
    let lastTarget = null;
    let timer = 0;
    const selector =
      "button,a,label,input,select,textarea,[role='button'],[aria-label]";
    const speak = (event) => {
      const target = event.target.closest?.(selector);
      if (
        !target ||
        target === lastTarget ||
        target.closest("[aria-hidden='true']")
      )
        return;
      lastTarget = target;
      const text = (
        target.getAttribute("aria-label") ||
        target.getAttribute("title") ||
        target.getAttribute("placeholder") ||
        target.innerText ||
        target.value ||
        ""
      )
        .replace(/\s+/g, " ")
        .trim();
      window.clearTimeout(timer);
      if (!text) return;
      timer = window.setTimeout(() => {
        window.speechSynthesis.cancel();
        const message = new SpeechSynthesisUtterance(text.slice(0, 240));
        message.lang =
          language === "en"
            ? "en-US"
            : language.startsWith("uz")
              ? "uz-UZ"
              : "ru-RU";
        window.speechSynthesis.speak(message);
      }, 250);
    };
    document.addEventListener("pointerover", speak);
    return () => {
      document.removeEventListener("pointerover", speak);
      window.clearTimeout(timer);
      window.speechSynthesis.cancel();
    };
  }, [soundGuide, language]);

  const active =
    view !== "normal" ||
    fontScale > 0 ||
    soundGuide ||
    underline ||
    reduceMotion ||
    largeCursor;
  const reset = () => {
    setView("normal");
    setFontScale(0);
    setSoundGuide(false);
    setUnderline(false);
    setReduceMotion(false);
    setLargeCursor(false);
  };

  return (
    <div className="tool-menu">
      <button
        className={`icon-button ${open || active ? "active" : ""}`}
        onClick={() => onOpenChange(!open)}
        aria-expanded={open}
        aria-label={tr("Специальные возможности")}
        title={tr("Специальные возможности")}
      >
        <Accessibility />
      </button>
      {open && (
        <section className="react-popover access-popover">
          <div className="popover-head">
            <div>
              <strong>{tr("Специальные возможности")}</strong>
              <small>{tr("Настройте отображение")}</small>
            </div>
            <button
              onClick={() => onOpenChange(false)}
              aria-label={tr("Закрыть меню")}
            >
              ×
            </button>
          </div>
          <fieldset className="access-view-options">
            <legend>{tr("Режим отображения")}</legend>
            {[
              ["normal", "Обычный"],
              ["whiteblack", "Чёрно-белый"],
              ["dark", "Тёмный"],
            ].map(([value, label]) => (
              <button
                type="button"
                key={value}
                className={view === value ? "active" : ""}
                onClick={() => setView(value)}
                aria-pressed={view === value}
              >
                <span>A</span>
                {tr(label)}
              </button>
            ))}
          </fieldset>
          <label className="scale-control">
            <span>
              {tr("Размер текста")} <b>{fontScale}%</b>
            </span>
            <input
              type="range"
              min="0"
              max="40"
              step="5"
              value={fontScale}
              onChange={(event) => setFontScale(Number(event.target.value))}
            />
          </label>
          <label>
            <input
              type="checkbox"
              checked={soundGuide}
              onChange={(event) => setSoundGuide(event.target.checked)}
            />
            {tr("Озвучивать при наведении")}
          </label>
          <label>
            <input
              type="checkbox"
              checked={underline}
              onChange={(event) => setUnderline(event.target.checked)}
            />
            {tr("Подчёркивать ссылки")}
          </label>
          <label>
            <input
              type="checkbox"
              checked={reduceMotion}
              onChange={(event) => setReduceMotion(event.target.checked)}
            />
            {tr("Уменьшить анимацию")}
          </label>
          <label>
            <input
              type="checkbox"
              checked={largeCursor}
              onChange={(event) => setLargeCursor(event.target.checked)}
            />
            {tr("Крупный курсор")}
          </label>
          <button className="reset-access" onClick={reset}>
            <RotateCcw />
            {tr("Сбросить")}
          </button>
        </section>
      )}
    </div>
  );
}
