"use client";

import { useEffect, useState } from "react";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import PublicApp from "./PublicApp";
import { MtuLoader } from "./MtuLoader";

export default function NextClient() {
  const [mounted, setMounted] = useState(false);
  const [language, setLanguage] = useState("ru");
  useEffect(() => {
    setMounted(true);
    setLanguage(
      new URLSearchParams(window.location.search).get("lang") || "ru",
    );
  }, []);

  return (
    <>
      {mounted && (
        <>
          <MtuLoader language={language} />
          <BrowserRouter basename="/app">
            {/^\/app\/(login|public)(\/|$)/.test(window.location.pathname) ? (
              <PublicApp />
            ) : (
              <App config={{ language: "ru", framework: "Next.js" }} />
            )}
          </BrowserRouter>
        </>
      )}
    </>
  );
}
