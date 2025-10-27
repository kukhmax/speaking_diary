import React, { createContext, useContext, useMemo, useState, useEffect } from 'react';
import en from './locales/en.json';
import ru from './locales/ru.json';

const translations = { en, ru };
const rtlLangs = ['ar', 'fa', 'he', 'ur'];

const I18nContext = createContext({
  lang: 'en',
  t: (key) => key,
  dir: 'ltr',
  setLang: () => {},
  uiLocale: 'en-US'
});

const getNested = (obj, path) => {
  return path.split('.').reduce((acc, part) => (acc && acc[part] !== undefined ? acc[part] : undefined), obj);
};

const localeMap = {
  en: 'en-US',
  ru: 'ru-RU'
};

export const I18nProvider = ({ children }) => {
  const [lang, setLang] = useState(() => {
    try {
      return localStorage.getItem('ui_lang') || 'ru';
    } catch {
      return 'ru';
    }
  });

  useEffect(() => {
    try { localStorage.setItem('ui_lang', lang); } catch {}
  }, [lang]);

  const t = useMemo(() => {
    return (key) => {
      const pack = translations[lang] || translations.en;
      const val = getNested(pack, key);
      if (val !== undefined) return val;
      const fallback = getNested(translations.en, key);
      return fallback !== undefined ? fallback : key;
    };
  }, [lang]);

  const dir = rtlLangs.includes(lang) ? 'rtl' : 'ltr';
  const uiLocale = localeMap[lang] || 'en-US';

  const value = useMemo(() => ({ lang, setLang, t, dir, uiLocale }), [lang, t, dir, uiLocale]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
};

export const useI18n = () => useContext(I18nContext);