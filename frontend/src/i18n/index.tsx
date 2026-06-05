"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from "react";

export type Locale = "zh-CN" | "en-US";

interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nContextValue>({
  locale: "zh-CN",
  setLocale: () => {},
  t: (key: string) => key,
});

// Lazy-loaded translations
const messages: Record<Locale, Record<string, string>> = {
  "zh-CN": {},
  "en-US": {},
};

async function loadLocale(locale: Locale): Promise<Record<string, string>> {
  if (Object.keys(messages[locale]).length > 0) return messages[locale];
  try {
    const data = await import(`./${locale}.json`);
    messages[locale] = data.default || data;
    return messages[locale];
  } catch {
    console.warn(`Failed to load locale: ${locale}`);
    return {};
  }
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("zh-CN");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("tech-chat-locale") as Locale | null;
    const detected = stored || navigator.language.startsWith("zh") ? "zh-CN" : "en-US";
    setLocaleState(detected);
    loadLocale(detected).then(() => setReady(true));
  }, []);

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    localStorage.setItem("tech-chat-locale", l);
    loadLocale(l).then(() => setReady(true));
  }, []);

  const t = useCallback(
    (key: string, params?: Record<string, string | number>) => {
      let text = messages[locale]?.[key] || messages["en-US"]?.[key] || key;
      if (params) {
        Object.entries(params).forEach(([k, v]) => {
          text = text.replace(`{${k}}`, String(v));
        });
      }
      return text;
    },
    [locale],
  );

  // Show nothing until translations are loaded (avoids flash of untranslated text)
  if (!ready) {
    return (
      <div
        style={{
          height: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "var(--bg)",
          color: "var(--text-muted)",
          fontSize: "0.9rem",
        }}
      >
        Loading...
      </div>
    );
  }

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useTranslation() {
  return useContext(I18nContext);
}
