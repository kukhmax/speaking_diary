import { api } from './client';

export type ReviewRequest = {
  text: string;
  ui_language: string; // e.g. 'pl'
};

export type ReviewResponse = {
  corrected_html: string;
  explanations_html: string;
  tts_audio_data_url?: string;
};

export async function postReview(payload: ReviewRequest) {
  const { data } = await api.post<ReviewResponse>('/review', payload);
  return data;
}