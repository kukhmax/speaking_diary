import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import Constants from 'expo-constants';
import en from './locales/en.json';
import pl from './locales/pl.json';
import ru from './locales/ru.json';

const extra = (Constants.expoConfig?.extra || {}) as { uiLanguage?: string };

i18n
  .use(initReactI18next)
  .init({
    lng: extra.uiLanguage || 'pl',
    fallbackLng: 'en',
    resources: {
      en: { translation: en },
      pl: { translation: pl },
      ru: { translation: ru },
    },
    interpolation: { escapeValue: false },
  });

export default i18n;