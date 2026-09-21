"use client";

import { useCallback, useEffect, useState } from "react";

const modes = ["auto", "system", "opposite"];
const read = (key) => {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
};
const save = (key, value) => {
  try {
    localStorage.setItem(key, value);
  } catch {}
};

function localDay(timeZone) {
  const parts = new Intl.DateTimeFormat("en", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());
  const values = Object.fromEntries(
    parts.map((part) => [part.type, part.value]),
  );
  return `${values.year}-${values.month}-${values.day}`;
}

function valid(schedule) {
  if (!schedule?.tzid || !schedule?.date) return false;
  try {
    return schedule.date === localDay(schedule.tzid);
  } catch {
    return false;
  }
}

function scheduleTheme(schedule) {
  if (!valid(schedule)) return null;
  if (schedule.sun_status === "midnight_sun") return "light";
  if (schedule.sun_status === "polar_night") return "dark";
  const rise = Date.parse(schedule.sunrise),
    set = Date.parse(schedule.sunset),
    now = Date.now();
  if (!Number.isFinite(rise) || !Number.isFinite(set)) return null;
  const light =
    rise <= set ? now >= rise && now < set : now >= rise || now < set;
  return light ? "light" : "dark";
}

async function locate() {
  const providers = [
    {
      url: "https://ipwho.is/",
      parse: (data) =>
        data.success === false
          ? null
          : { lat: data.latitude, lng: data.longitude },
    },
    {
      url: "https://ipapi.co/json/",
      parse: (data) =>
        data.error ? null : { lat: data.latitude, lng: data.longitude },
    },
  ];
  for (const provider of providers) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 7000);
    try {
      const response = await fetch(provider.url, {
        signal: controller.signal,
        credentials: "omit",
        referrerPolicy: "no-referrer",
      });
      if (!response.ok) continue;
      const result = provider.parse(await response.json());
      if (
        result &&
        Number.isFinite(Number(result.lat)) &&
        Number.isFinite(Number(result.lng))
      )
        return {
          lat: Number(Number(result.lat).toFixed(2)),
          lng: Number(Number(result.lng).toFixed(2)),
        };
    } catch {
    } finally {
      clearTimeout(timer);
    }
  }
  return { lat: 41.31, lng: 69.24 };
}

export function useSolarTheme(language = "ru") {
  const [mode, setMode] = useState(() =>
    modes.includes(read("mtu-theme-cycle")) ? read("mtu-theme-cycle") : "auto",
  );
  const [theme, setTheme] = useState(
    () => read("mtu-theme") || read("mtu-react-theme") || "dark",
  );
  const [schedule, setSchedule] = useState(() => {
    try {
      return JSON.parse(read("mtu-solar-schedule") || "null");
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(false);
  const [retryAt, setRetryAt] = useState(0);
  const apply = useCallback((next) => {
    setTheme(next);
    document.documentElement.dataset.reactTheme = next;
    save("mtu-theme", next);
    save("mtu-react-theme", next);
  }, []);

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const update = () => {
      if (mode === "auto")
        apply(scheduleTheme(schedule) || (media.matches ? "dark" : "light"));
      else if (mode === "system") apply(media.matches ? "dark" : "light");
      else apply(media.matches ? "light" : "dark");
    };
    update();
    media.addEventListener("change", update);
    const timer = setInterval(update, 30000);
    return () => {
      media.removeEventListener("change", update);
      clearInterval(timer);
    };
  }, [mode, schedule, apply]);

  useEffect(() => {
    if (mode !== "auto" || valid(schedule) || loading || Date.now() < retryAt)
      return;
    let active = true;
    setLoading(true);
    (async () => {
      try {
        const location = await locate();
        const params = new URLSearchParams({
          ...location,
          date: "today",
          time_format: "iso8601",
        });
        const response = await fetch(
          `https://api.sunrise-sunset.org/v2?${params}`,
          { credentials: "omit", referrerPolicy: "no-referrer" },
        );
        if (!response.ok) throw new Error();
        const data = await response.json();
        if (data.error || !valid(data)) throw new Error();
        if (!active) return;
        const next = {
          date: data.date,
          tzid: data.tzid,
          sunrise: data.sunrise,
          sunset: data.sunset,
          sun_status: data.sun_status,
        };
        save("mtu-solar-schedule", JSON.stringify(next));
        setRetryAt(0);
        setSchedule(next);
      } catch {
        if (active) setRetryAt(Date.now() + 15 * 60 * 1000);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [mode, schedule, loading, retryAt]);

  const cycle = () => {
    const next = modes[(modes.indexOf(mode) + 1) % modes.length];
    setMode(next);
    save("mtu-theme-cycle", next);
  };
  const format = (value) =>
    value && schedule?.tzid
      ? new Intl.DateTimeFormat(language, {
          timeZone: schedule.tzid,
          hour: "2-digit",
          minute: "2-digit",
        }).format(new Date(value))
      : "—";
  return {
    mode,
    theme,
    cycle,
    loading,
    schedule,
    details: valid(schedule)
      ? `${format(schedule.sunrise)} · ${format(schedule.sunset)} (${schedule.tzid})`
      : "",
  };
}
