import axios from 'axios';
import Constants from 'expo-constants';

const extra = (Constants.expoConfig?.extra || {}) as { apiBase?: string };
const API_BASE = extra.apiBase || 'https://app.diary.pw-new.club/api';

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 20000,
});

export const setAuthToken = (token?: string) => {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common['Authorization'];
  }
};