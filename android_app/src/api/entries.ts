import { api } from './client';

export type Entry = {
  id: string;
  text: string;
  created_at: string;
};

export async function listEntries() {
  const { data } = await api.get<Entry[]>('/entries');
  return data;
}

export async function createEntry(text: string) {
  const { data } = await api.post<Entry>('/entries', { text });
  return data;
}