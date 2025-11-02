import { api } from './client';

export async function transcribeAudio(uri: string, uiLanguage: string) {
  // NOTE: Expo fetch/axios + multipart; здесь только сигнатура
  // Реальная отправка файла будет реализована позже
  return api.post('/transcribe', { uri, ui_language: uiLanguage });
}