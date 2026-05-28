import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './locales/en.json';
import ja from './locales/ja.json';
import af from './locales/af.json';
import zul from './locales/zul.json';
import xho from './locales/xho.json';
import sot from './locales/sot.json';
import tsn from './locales/tsn.json';

export const availableLocales = ['en', 'af', 'zul', 'xho', 'sot', 'tsn', 'ja'] as const;
export type AvailableLocale = (typeof availableLocales)[number];

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    ja: { translation: ja },
    af: { translation: af },
    zul: { translation: zul },
    xho: { translation: xho },
    sot: { translation: sot },
    tsn: { translation: tsn },
  },
  lng: 'en',
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
  returnNull: false,
  returnEmptyString: false,
});

export default i18n;
