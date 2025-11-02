import { api } from './client';

export async function transcribeAudio(uri: string, language: string = 'auto') {
  const form = new FormData();
  // RN FormData file
  form.append('audio', {
    // @ts-ignore RN file shape
    uri,
    name: 'record.m4a',
    type: 'audio/m4a',
  });
  form.append('language', language);

  const { data } = await api.post<{ text: string; language: string }>('/transcribe', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}