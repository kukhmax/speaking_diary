import { api } from './client';

export async function translateUI(text: string, targetLang: string) {
  const { data } = await api.post<{ translated: string }>('/translate', {
    text,
    target_language: targetLang,
  });
  return data.translated;
}