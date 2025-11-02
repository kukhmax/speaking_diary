import 'dotenv/config';
import type { ExpoConfig } from '@expo/config-types';

const config: ExpoConfig = {
  name: 'Voice Diary',
  slug: 'voice-diary-android',
  version: '0.1.0',
  orientation: 'portrait',
  icon: './assets/icon.png',
  splash: {
    image: './assets/splash.png',
    resizeMode: 'contain',
    backgroundColor: '#ffffff',
  },
  assetBundlePatterns: ['**/*'],
  android: {
    package: 'pw.club.diary.app',
    permissions: ['RECORD_AUDIO'],
  },
  extra: {
    apiBase: process.env.API_BASE || 'https://app.diary.pw-new.club/api',
    uiLanguage: process.env.UI_LANGUAGE || 'pl',
  },
};

export default config;