import React, { useState, useEffect, useRef } from 'react';
import { Mic, Save, X, Plus, ChevronDown, ChevronRight, Square, Play, Trash2, MoreVertical } from 'lucide-react';
import { useI18n } from './i18n';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const DiaryApp = () => {
  const { lang, t, dir, uiLocale, setLang } = useI18n();
  const [entries, setEntries] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [currentText, setCurrentText] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('ru-RU');
  const [isProcessing, setIsProcessing] = useState(false);
  const [expandedDates, setExpandedDates] = useState(new Set());
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [reviewModal, setReviewModal] = useState({ visible: false, data: null });
  const [audioModal, setAudioModal] = useState({ visible: false, src: null, title: '' });
  const [explainModal, setExplainModal] = useState({ visible: false, html: '' });
  const [settingsModal, setSettingsModal] = useState(false);
  const [pendingLang, setPendingLang] = useState(lang);
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const [auth, setAuth] = useState(() => {
    try {
      const activeKey = localStorage.getItem('auth_active') || '';
      const map = JSON.parse(localStorage.getItem('auth_accounts') || '{}');
      return activeKey && map[activeKey] ? map[activeKey] : null;
    } catch { return null; }
  });
  
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const audioRef = useRef(null);
  const streamRef = useRef(null);

  // Authentication helpers (multi-account)
  const loadAccounts = () => {
    try { return JSON.parse(localStorage.getItem('auth_accounts') || '{}'); } catch { return {}; }
  };
  const saveAccounts = (obj) => {
    try { localStorage.setItem('auth_accounts', JSON.stringify(obj)); } catch {}
  };
  const setActiveAccount = (key) => { try { localStorage.setItem('auth_active', key || ''); } catch {} };
  const activeToken = () => {
    try {
      const activeKey = localStorage.getItem('auth_active');
      const map = loadAccounts();
      return activeKey && map[activeKey] ? map[activeKey].access_token : null;
    } catch { return null; }
  };
  const authFetch = async (url, options = {}) => {
    const token = activeToken();
    const headers = new Headers(options.headers || {});
    if (token) headers.set('Authorization', `Bearer ${token}`);
    const resp = await fetch(url, { ...options, headers, credentials: 'include' });
    if (resp.status === 401) {
      setAuth(null);
    }
    return resp;
  };
  const switchAccount = async (key) => {
    const map = loadAccounts();
    const rec = map[key];
    if (!rec) return;
    try {
      await fetch(`${API_BASE}/auth/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ access_token: rec.access_token })
      });
    } catch {}
    setActiveAccount(key);
    setAuth(rec);
    await loadEntries();
  };
  const logout = async () => {
    try { await fetch(`${API_BASE}/auth/logout`, { method: 'POST', credentials: 'include' }); } catch {}
    try { localStorage.removeItem('auth_active'); } catch {}
    setAuth(null);
  };
  const storeAccount = (user, token) => {
    const key = user?.telegram_id ? `tg:${user.telegram_id}` : `id:${user?.id || Date.now()}`;
    const map = loadAccounts();
    map[key] = { user, access_token: token, ts: Date.now() };
    saveAccounts(map);
    setActiveAccount(key);
    setAuth(map[key]);
    return key;
  };
  const tryTelegramAuth = async () => {
    try {
      const tg = window?.Telegram?.WebApp;
      const initData = tg?.initData || '';
      if (!initData) return null;
      const resp = await fetch(`${API_BASE}/auth/telegram`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ init_data: initData })
      });
      if (!resp.ok) return null;
      const data = await resp.json();
      const key = storeAccount(data.user, data.access_token);
      await loadEntries();
      return key;
    } catch (e) {
      console.warn('Telegram auth failed', e);
      return null;
    }
  };

  // Fallback: авторизация по токену сессии, переданному через параметр URL (?session=...)
  const tryTelegramSessionAuth = async () => {
    try {
      const params = new URLSearchParams(window.location.search || '');
      const session = params.get('session');
      if (!session) return null;
      const resp = await fetch(`${API_BASE}/auth/telegram/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ session })
      });
      if (!resp.ok) return null;
      const data = await resp.json();
      const key = storeAccount(data.user, data.access_token);
      await loadEntries();
      return key;
    } catch (e) {
      console.warn('Telegram session auth failed', e);
      return null;
    }
  };

  // Review & Audio storage helpers
  const REVIEW_PREFIX = 'entry_review:';
  const AUDIO_PREFIX = 'entry_audio:';
  const saveReviewLegacy = (id, obj) => { try { localStorage.setItem(REVIEW_PREFIX + id, JSON.stringify(obj)); } catch {} };
  const loadReviewLegacy = (id) => { try { const s = localStorage.getItem(REVIEW_PREFIX + id); return s ? JSON.parse(s) : null; } catch { return null; } };
  const saveReviewForLang = (id, obj, uiLang) => { try { localStorage.setItem(`${REVIEW_PREFIX}${id}:${uiLang}`, JSON.stringify(obj)); } catch {} };
  const loadReviewForLang = (id, uiLang) => { try { const s = localStorage.getItem(`${REVIEW_PREFIX}${id}:${uiLang}`); if (s) return JSON.parse(s); const legacy = localStorage.getItem(REVIEW_PREFIX + id); return legacy ? JSON.parse(legacy) : null; } catch { return null; } };
  const blobToDataUrl = (blob) => new Promise((resolve, reject) => { const r = new FileReader(); r.onloadend = () => resolve(r.result); r.onerror = reject; r.readAsDataURL(blob); });
  const saveAudio = async (id, blob) => { try { const url = await blobToDataUrl(blob); localStorage.setItem(AUDIO_PREFIX + id, url); } catch {} };
  const loadAudio = (id) => { try { return localStorage.getItem(AUDIO_PREFIX + id); } catch { return null; } };
  const fixHtmlSpaces = (html) => {
    if (!html) return html;
    try {
      return html
        .replace(/([\p{L}\p{N}])<mark/gu, '$1 <mark')
        .replace(/<\/mark>([\p{L}\p{N}])/gu, '</mark> $1')
        .replace(/([.!?])(?=[^\s<])/g, '$1 ');
    } catch {
      return html;
    }
  };
  const removeReview = (id) => { try { localStorage.removeItem(REVIEW_PREFIX + id); Object.keys(localStorage).forEach(k => { if (k.startsWith(`${REVIEW_PREFIX}${id}:`)) localStorage.removeItem(k); }); } catch {} };
  const removeAudio = (id) => { try { localStorage.removeItem(AUDIO_PREFIX + id); } catch {} };
  const normalizeSpeechLang = (lang) => {
    const lower = (lang || '').toLowerCase();
    if (lower.startsWith('ru')) return 'ru-RU';
    if (lower.startsWith('pt')) return 'pt-PT';
    if (lower.startsWith('es')) return 'es-ES';
    if (lower.startsWith('pl')) return 'pl-PL';
    if (lower.startsWith('en')) return 'en-US';
    return lang || 'en-US';
  };
  const ensureVoices = () => new Promise((resolve) => {
    const list = window.speechSynthesis.getVoices();
    if (list && list.length) return resolve(list);
    const handler = () => {
      const ready = window.speechSynthesis.getVoices();
      window.speechSynthesis.removeEventListener('voiceschanged', handler);
      resolve(ready || []);
    };
    window.speechSynthesis.addEventListener('voiceschanged', handler);
  });
  const pickVoice = (voices, lang) => {
    const base = (lang || '').toLowerCase().split('-')[0];
    const exact = voices.find(v => (v.lang || '').toLowerCase() === (lang || '').toLowerCase());
    if (exact) return exact;
    const byBase = voices.find(v => (v.lang || '').toLowerCase().startsWith(base));
    if (byBase) return byBase;
    const byName = voices.find(v => /\bru\b|russian|русский|\bpt\b|portuguese|português|\bes\b|spanish|español|\bpl\b|polish|polski/i.test((v.name || '') + ' ' + (v.lang || '')));
    return byName || null;
  };
  const speakText = async (text, lang) => {
    const useLang = normalizeSpeechLang(lang);
    const utter = new SpeechSynthesisUtterance(text);
    try {
      let voices = window.speechSynthesis.getVoices();
      if (!voices || voices.length === 0) {
        voices = await ensureVoices();
      }
      const v = pickVoice(voices || [], useLang);
      if (v) {
        utter.voice = v;
        utter.lang = v.lang || useLang;
      } else {
        // Fallback: использовать запрошенный язык, даже если голос не найден
        utter.lang = useLang;
      }
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utter);
    } catch (e) {
      console.error('TTS error:', e);
      window.speechSynthesis.cancel();
      utter.lang = useLang;
      window.speechSynthesis.speak(utter);
    }
  };

  const getFlagSrc = (code) => {
    const lower = (code || '').toLowerCase();
    const match = languages.find(l => l.code.toLowerCase() === lower || l.code.toLowerCase().startsWith(lower.split('-')[0]));
    return (match && match.flagSrc) || '/flags/us.svg';
  };

  const handleDeleteEntry = async (entry) => {
    try {
      if (entry.isOffline) {
        const filtered = getOfflineEntries().filter(e => e.id !== entry.id);
        setOfflineEntries(filtered);
        removeReview(entry.id);
        removeAudio(entry.id);
        setEntries(prev => prev.filter(e => e.id !== entry.id));
        return;
      }
      const resp = await authFetch(`${API_BASE}/entries/${entry.id}`, { method: 'DELETE' });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      removeReview(entry.id);
      removeAudio(entry.id);
      setEntries(prev => prev.filter(e => e.id !== entry.id));
    } catch (err) {
      console.error('Delete entry failed:', err);
      alert(t('alerts.delete_failed'));
    }
  };
  const migrateLocalData = (oldId, newId) => { try { const r = loadReviewLegacy(oldId); if (r) saveReviewLegacy(newId, r); const a = loadAudio(oldId); if (a) localStorage.setItem(AUDIO_PREFIX + newId, a); localStorage.removeItem(REVIEW_PREFIX + oldId); localStorage.removeItem(AUDIO_PREFIX + oldId); } catch {} };

  const openReview = (entry) => {
    const rev = loadReviewForLang(entry.id, lang);
    const audioUri = loadAudio(entry.id);
    setReviewModal({
      visible: true,
      data: {
        entryId: entry.id,
        original: rev?.original_text || entry.text,
        correctedHtml: fixHtmlSpaces(rev?.corrected_html) || entry.text,
        correctedText: rev?.corrected_text || entry.text,
        explanationsHtml: rev?.explanations_html || '',
        audioUri,
        ttsUri: rev?.tts_audio_data_url || null,
        language: rev?.language || entry.language
      }
    });
    if (!rev) {
      (async () => {
        try {
      const resp = await authFetch(`${API_BASE}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: entry.text, language: entry.language, ui_language: lang })
      });
          if (resp.ok) {
            const revObj = await resp.json();
            saveReviewForLang(entry.id, { ...revObj, original_text: entry.text }, lang);
            setReviewModal(prev => {
              if (!prev.visible || prev.data?.entryId !== entry.id) return prev;
              return {
                visible: true,
                data: {
                  ...prev.data,
                  correctedHtml: fixHtmlSpaces(revObj?.corrected_html) || entry.text,
                  correctedText: revObj?.corrected_text || entry.text,
                  explanationsHtml: revObj?.explanations_html || '',
                  ttsUri: revObj?.tts_audio_data_url || null
                }
              };
            });
          }
        } catch (e) {
          console.error('Lazy review fetch failed:', e);
        }
      })();
    }
  };
  const closeReviewModal = () => setReviewModal({ visible: false, data: null });

  // Mobile-friendly modals for compact UI
  const openAudioModal = (src, title = t('modals.tts_title')) => setAudioModal({ visible: true, src, title });
  const closeAudioModal = () => setAudioModal({ visible: false, src: null, title: '' });
  const openExplainModal = (html) => setExplainModal({ visible: true, html });
  const closeExplainModal = () => setExplainModal({ visible: false, html: '' });

  useEffect(() => {
    (async () => {
      const tg = window?.Telegram?.WebApp;
      if (tg && tg.initData) {
        const ok = await tryTelegramAuth();
        if (!ok) {
          // Если проверка initData не прошла (например, неверный токен бота на бэкенде), пробуем session
          await tryTelegramSessionAuth();
        }
      } else {
        // Открытие вне Telegram: пробуем session, затем восстановление локального токена
        const sessOk = await tryTelegramSessionAuth();
        if (!sessOk) {
          try {
            const token = activeToken();
            if (token) {
              await fetch(`${API_BASE}/auth/select`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ access_token: token })
              });
            }
          } catch {}
        }
      }
      await loadEntries();
    })();
    return () => {
      stopRecording();
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Update list corrected HTML when UI language changes
  useEffect(() => {
    setEntries(prev => prev.map(e => {
      const rev = loadReviewForLang(e.id, lang);
      return { ...e, textHtml: fixHtmlSpaces(rev?.corrected_html) || null };
    }));
  }, [lang]);

  // Re-fetch review/explanations for open modal when language changes
  useEffect(() => {
    if (reviewModal.visible && reviewModal.data?.entryId) {
      const entryId = reviewModal.data.entryId;
      const entry = entries.find(e => e.id === entryId);
      const rev = loadReviewForLang(entryId, lang);
      if (rev) {
        setReviewModal(prev => ({
          visible: true,
          data: {
            ...prev.data,
            original: rev?.original_text || entry?.text || prev.data?.original || '',
            correctedHtml: fixHtmlSpaces(rev?.corrected_html) || entry?.text || prev.data?.correctedHtml || '',
            correctedText: rev?.corrected_text || entry?.text || prev.data?.correctedText || '',
            explanationsHtml: rev?.explanations_html || '',
            ttsUri: rev?.tts_audio_data_url || null
          }
        }));
      } else if (entry) {
        (async () => {
          try {
      const resp = await authFetch(`${API_BASE}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: entry.text, language: entry.language, ui_language: lang })
      });
            if (resp.ok) {
              const revObj = await resp.json();
              saveReviewForLang(entry.id, { ...revObj, original_text: entry.text }, lang);
              setReviewModal(prev => ({
                visible: true,
                data: {
                  ...prev.data,
                  correctedHtml: fixHtmlSpaces(revObj?.corrected_html) || entry.text,
                  correctedText: revObj?.corrected_text || entry.text,
                  explanationsHtml: revObj?.explanations_html || '',
                  ttsUri: revObj?.tts_audio_data_url || null
                }
              }));
            }
          } catch (e) {
            console.error('Review fetch on language change failed:', e);
          }
        })();
      }
    }
  }, [lang]);

  // Offline storage helpers
  const OFFLINE_KEY = 'offline_entries';
  const getOfflineEntries = () => {
    try { return JSON.parse(localStorage.getItem(OFFLINE_KEY) || '[]'); } catch { return []; }
  };
  const setOfflineEntries = (entries) => {
    try { localStorage.setItem(OFFLINE_KEY, JSON.stringify(entries)); } catch {}
  };

  const loadEntries = async () => {
    try {
      const response = await authFetch(`${API_BASE}/entries?per_page=50`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      const serverEntries = (data.entries || []).map(e => {
        const rev = loadReviewForLang(e.id, lang);
        return {
          id: e.id,
          text: e.text,
          textHtml: fixHtmlSpaces(rev?.corrected_html) || null,
          timestamp: e.timestamp,
          language: e.language,
          duration: e.audio_duration,
          isOffline: false
        };
      });
      const offlineEntries = getOfflineEntries().map(e => {
        const rev = loadReviewForLang(e.id, lang);
        return { ...e, textHtml: fixHtmlSpaces(rev?.corrected_html) || null };
      });
      const combined = [...serverEntries, ...offlineEntries].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      setEntries(combined);
    } catch (error) {
      console.error('Error loading entries:', error);
      const offlineEntries = getOfflineEntries();
      setEntries(offlineEntries);
    }
  };

  const syncOfflineEntries = async () => {
    const offlineEntries = getOfflineEntries();
    if (!offlineEntries.length) return;

    const remaining = [];
    for (const item of offlineEntries) {
      try {
        const response = await authFetch(`${API_BASE}/entries`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: item.text,
            language: item.language,
            audio_duration: item.duration
          })
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const saved = await response.json();
        migrateLocalData(item.id, saved.id);
        // После сохранения на сервере запускаем проверку
        try {
          const revResp = await authFetch(`${API_BASE}/review`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: saved.text, language: saved.language, ui_language: lang })
          });
          if (revResp.ok) {
            const revObj = await revResp.json();
            saveReviewForLang(saved.id, { ...revObj, original_text: saved.text }, lang);
          }
        } catch (e) {
          console.error('Review failed during sync:', e);
        }
        const rev = loadReviewForLang(saved.id, lang);
        const normalized = {
          id: saved.id,
          text: saved.text,
          textHtml: fixHtmlSpaces(rev?.corrected_html) || null,
          timestamp: saved.timestamp,
          language: saved.language,
          duration: saved.audio_duration,
          isOffline: false
        };
        setEntries(prev => [normalized, ...prev.filter(e => e.id !== item.id)]);
      } catch (err) {
        console.error('Sync offline entry failed:', err);
        remaining.push(item);
      }
    }
    setOfflineEntries(remaining);
  };

  useEffect(() => {
    const handleOnline = () => {
      syncOfflineEntries();
      loadEntries();
    };
    window.addEventListener('online', handleOnline);
    // Try syncing on mount as well
    syncOfflineEntries();
    return () => {
      window.removeEventListener('online', handleOnline);
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
        }

        // Автоматическая транскрибация
        await transcribeAudio(blob);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert(t('alerts.mic_failed'));
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const transcribeAudio = async (blob) => {
    setIsProcessing(true);
    setCurrentText(t('actions.transcribing'));

    try {
      const formData = new FormData();
      formData.append('audio', blob, 'recording.webm');
      
      // Преобразуем язык из формата браузера в формат Groq
      const languageMap = {
        'ru-RU': 'ru',
        'en-US': 'en',
        'pt-PT': 'pt',
        'es-ES': 'es',
        'pl-PL': 'pl'
      };
      
      const groqLanguage = languageMap[selectedLanguage] || 'auto';
      formData.append('language', groqLanguage);
      
      const response = await authFetch(`${API_BASE}/transcribe`, {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }
      
      setCurrentText(data.text || t('alerts.transcription_failed'));
      setIsProcessing(false);

    } catch (error) {
      console.error('Transcription error:', error);
      setCurrentText(`${t('alerts.transcription_error_prefix')}: ${error.message}. ${t('alerts.transcription_error_hint')}`);
      setIsProcessing(false);
    }
  };

  const playAudio = () => {
    if (audioBlob && !isPlaying) {
      const url = URL.createObjectURL(audioBlob);
      audioRef.current = new Audio(url);
      audioRef.current.play();
      setIsPlaying(true);

      audioRef.current.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(url);
      };
    }
  };

  const deleteAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setAudioBlob(null);
    setIsPlaying(false);
    setCurrentText('');
    setRecordingTime(0);
  };

  const saveEntry = async () => {
    if (!currentText.trim()) return;

    setIsProcessing(true);
    const timestamp = new Date().toISOString();

    try {
      const response = await authFetch(`${API_BASE}/entries`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: currentText.trim(),
          language: selectedLanguage,
          audio_duration: recordingTime
        })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const saved = await response.json();

      // Проверка и исправление текста через backend
      try {
        const revResp = await authFetch(`${API_BASE}/review`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: saved.text, language: saved.language, ui_language: lang })
        });
        if (revResp.ok) {
          const rev = await revResp.json();
          saveReviewForLang(saved.id, { ...rev, original_text: saved.text }, lang);
        }
      } catch (e) {
        console.error('Review request failed:', e);
      }

      // Сохраняем аудио локально под id записи
      if (audioBlob) {
        try { await saveAudio(saved.id, audioBlob); } catch {}
      }

      const rev = loadReviewForLang(saved.id, lang);
      const normalized = {
        id: saved.id,
        text: saved.text,
        textHtml: fixHtmlSpaces(rev?.corrected_html) || null,
        timestamp: saved.timestamp,
        language: saved.language,
        duration: saved.audio_duration,
        isOffline: false
      };

      setEntries(prev => [normalized, ...prev]);
      setCurrentText('');
      setAudioBlob(null);
      setRecordingTime(0);
      setShowModal(false);
    } catch (error) {
      console.error('Error saving entry:', error);
      // Fallback: сохраняем офлайн
      const offlineId = `offline_${Date.now()}`;
      const offlineEntry = {
        tempId: offlineId,
        id: offlineId,
        text: currentText.trim(),
        textHtml: null,
        timestamp,
        language: selectedLanguage,
        duration: recordingTime,
        isOffline: true
      };
      const offlineEntries = getOfflineEntries();
      setOfflineEntries([offlineEntry, ...offlineEntries]);
      setEntries(prev => [offlineEntry, ...prev]);
      if (audioBlob) {
        try { await saveAudio(offlineId, audioBlob); } catch {}
      }
      alert(t('alerts.saved_offline'));
      setShowModal(false);
      setCurrentText('');
      setAudioBlob(null);
      setRecordingTime(0);
    } finally {
      setIsProcessing(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const groupEntriesByDate = () => {
    const grouped = {};
    entries.forEach(entry => {
      const date = new Date(entry.timestamp).toLocaleDateString(uiLocale, {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
      if (!grouped[date]) grouped[date] = [];
      grouped[date].push(entry);
    });
    return grouped;
  };

  const toggleDate = (date) => {
    const newExpanded = new Set(expandedDates);
    if (newExpanded.has(date)) {
      newExpanded.delete(date);
    } else {
      newExpanded.add(date);
    }
    setExpandedDates(newExpanded);
  };

  const groupedEntries = groupEntriesByDate();
  const languages = [
    { code: 'ru-RU', name: 'Русский', flagSrc: '/flags/ru.svg' },
    { code: 'en-US', name: 'English', flagSrc: '/flags/us.svg' },
    { code: 'pt-PT', name: 'Português', flagSrc: '/flags/pt.svg' },
    { code: 'es-ES', name: 'Español', flagSrc: '/flags/es.svg' },
    { code: 'pl-PL', name: 'Polski', flagSrc: '/flags/pl.svg' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900" dir={dir}>
      <div className="bg-black bg-opacity-30 backdrop-blur-md border-b border-purple-500/20">
        <div className="max-w-2xl mx-auto px-3 sm:px-4 py-4 sm:py-6">
          <div className="flex items-center justify-between relative">
            <button
              className="flex-1 flex justify-start text-purple-300 hover:text-purple-200"
              aria-label={t('modals.ui_language_title')}
              onClick={() => { setPendingLang(lang); setSettingsModal(true); }}
            >
              <MoreVertical size={22} />
            </button>
            <h1 className="text-2xl sm:text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400 text-center">
              {t('header.title')}
            </h1>
            <div className="flex-1 flex justify-end">
              <div className="relative">
                <button
                  onClick={() => setAccountMenuOpen(v => !v)}
                  className="text-xs sm:text-sm px-2 py-1 rounded-md bg-slate-800/60 text-purple-100 border border-purple-500/30 hover:bg-slate-700/60"
                >
                  {auth?.user?.username ? `@${auth.user.username}` : (auth?.user?.telegram_id ? `tg:${auth.user.telegram_id}` : (t('actions.sign_in') || 'Войти'))}
                </button>
                {accountMenuOpen && (
                  <div className="absolute right-0 mt-2 w-56 bg-slate-900/95 border border-purple-500/30 rounded-md shadow-lg z-50 p-2">
                    <div className="text-xs text-purple-300 mb-1">{t('header.title')} — аккаунты</div>
                    {Object.entries(loadAccounts()).length ? (
                      <div className="max-h-60 overflow-auto space-y-1">
                        {Object.entries(loadAccounts()).map(([key, rec]) => (
                          <button
                            key={key}
                            onClick={() => { setAccountMenuOpen(false); switchAccount(key); }}
                            className="w-full text-left px-2 py-1.5 rounded hover:bg-purple-500/10 text-purple-100"
                          >
                            {rec?.user?.username ? `@${rec.user.username}` : (rec?.user?.telegram_id ? `tg:${rec.user.telegram_id}` : key)}
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div className="text-purple-300/70 text-sm px-2 py-1.5">{t('actions.no_entries')}</div>
                    )}
                    <div className="mt-2 border-t border-purple-500/20 pt-2 flex gap-2">
                      <button
                        onClick={async () => { setAccountMenuOpen(false); await tryTelegramAuth(); await loadEntries(); }}
                        className="flex-1 text-xs px-2 py-1 rounded bg-purple-600 text-white hover:bg-purple-500"
                      >
                        Telegram Login
                      </button>
                      {auth?.user ? (
                        <button
                          onClick={() => { setAccountMenuOpen(false); logout(); }}
                          className="text-xs px-2 py-1 rounded bg-slate-700 text-purple-100 border border-purple-500/30 hover:bg-slate-600"
                        >
                          {t('actions.logout') || 'Выход'}
                        </button>
                      ) : null}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
          <p className="text-purple-300/70 text-xs sm:text-sm mt-1 text-center">{t('header.subtitle')}</p>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-3 sm:px-4 py-4 sm:py-6">
        <button
          onClick={() => setShowModal(true)}
          className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-2xl py-3 px-4 sm:py-4 sm:px-6 flex items-center justify-center gap-2 sm:gap-3 shadow-lg shadow-purple-500/30 transition-all mb-4 sm:mb-6"
        >
          <Plus size={22} />
          <span className="text-base sm:text-lg font-semibold">{t('actions.create_entry')}</span>
        </button>

        <div className="space-y-3">
          {Object.keys(groupedEntries).length === 0 ? (
            <div className="text-center py-12 text-purple-300/50">
              <p>{t('actions.no_entries')}</p>
              <p className="text-sm mt-2">{t('actions.click_create_to_start')}</p>
            </div>
          ) : (
            Object.entries(groupedEntries).map(([date, dateEntries]) => (
              <div key={date} className="bg-black bg-opacity-30 backdrop-blur-md rounded-xl border border-purple-500/20 overflow-hidden">
                <button
                  onClick={() => toggleDate(date)}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-purple-500/10 transition-colors"
                >
                  <span className="text-purple-200 font-medium">{date}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-purple-400/60 text-sm">{dateEntries.length}</span>
                    {expandedDates.has(date) ? (
                      <ChevronDown size={20} className="text-purple-400" />
                    ) : (
                      <ChevronRight size={20} className="text-purple-400" />
                    )}
                  </div>
                </button>
                
                {expandedDates.has(date) && (
                  <div className="border-t border-purple-500/20 divide-y divide-purple-500/10">
                    {dateEntries.map((entry) => (
                      <div key={entry.id} className="px-4 py-3 hover:bg-purple-500/5">
                        <div className="flex justify-between items-start mb-1">
                          <div className="flex items-center gap-2">
                            <div className="text-sm text-purple-400/60">
                              {new Date(entry.timestamp).toLocaleTimeString(uiLocale, {
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </div>
                            {entry.isOffline && (
                              <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-300 border border-yellow-500/30">
                                {t('labels.offline')}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-3">
                            {entry.duration && (
                              <div className="text-xs text-purple-400/40">
                                {formatTime(entry.duration)}
                              </div>
                            )}
                            <button
                              onClick={(e) => { e.stopPropagation(); handleDeleteEntry(entry); }}
                              className="text-purple-400 hover:text-pink-300"
                              aria-label={t('actions.delete_entry_aria')}
                            >
                              <X size={18} />
                            </button>
                          </div>
                        </div>
                        <div className="flex items-start gap-2">
                          <img src={getFlagSrc(entry.language)} alt={entry.language} className="h-4 w-6 rounded-sm border border-purple-500/30 mt-1" />
                          {entry.textHtml ? (
                            <div
                              className="entry-text text-purple-100 leading-relaxed cursor-pointer"
                              onClick={() => openReview(entry)}
                              dangerouslySetInnerHTML={{ __html: entry.textHtml }}
                            />
                          ) : (
                            <div
                              className="text-purple-100 leading-relaxed cursor-pointer"
                              onClick={() => openReview(entry)}
                            >
                              {entry.text}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 z-50">
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl max-w-md w-full border border-purple-500/30 shadow-2xl">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl sm:text-2xl font-bold text-purple-200">{t('modals.new_entry')}</h2>
                <button onClick={() => setShowModal(false)} className="text-purple-400 hover:text-purple-300"><X size={24} /></button>
              </div>

              <div className="space-y-4">
                <div>
                  <div className="text-sm text-purple-300 mb-1">{t('labels.language')}</div>
                  {(() => {
                    const currentLang = languages.find(l => l.code === selectedLanguage) || languages[0];
                    return (
                      <div className="flex items-center gap-2 mb-2">
                        <img src={currentLang.flagSrc} alt={currentLang.name} className="h-5 w-7 rounded-sm border border-purple-500/30" />
                        <span className="text-purple-200">{currentLang.name}</span>
                      </div>
                    );
                  })()}
                  <select
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    className="w-full bg-slate-700/50 text-purple-100 rounded-md p-3 border border-purple-500/30"
                  >
                    {languages.map(l => (
                      <option key={l.code} value={l.code}>{l.name}</option>
                    ))}
                  </select>
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <div className="flex items-center gap-2 sm:gap-3">
                    {isRecording ? (
                      <button
                        onClick={stopRecording}
                        className="px-4 py-2 rounded-md bg-red-600 text-white flex items-center gap-2 hover:bg-red-700"
                      >
                        <Square size={18} /> <span className="hidden sm:inline">{t('actions.stop')}</span>
                        <span className="sr-only">{t('actions.stop')}</span>
                      </button>
                    ) : (
                      <button
                        onClick={startRecording}
                        className="px-4 py-2 rounded-md bg-purple-600 text-white flex items-center gap-2 hover:bg-purple-700"
                      >
                        <Mic size={18} /> <span className="hidden sm:inline">{t('actions.record')}</span>
                        <span className="sr-only">{t('actions.record')}</span>
                      </button>
                    )}
                    <span className="text-purple-300 text-sm sm:text-base">{formatTime(recordingTime)}</span>
                  </div>

                  {audioBlob && (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={playAudio}
                        className="px-3 py-2 rounded-md bg-slate-700/50 text-purple-100 flex items-center gap-2 border border-purple-500/30 hover:bg-slate-700"
                        aria-label={t('actions.listen')}
                      >
                        <Play size={18} />
                        <span className="hidden sm:inline">{t('actions.listen')}</span>
                        <span className="sr-only">{t('actions.listen')}</span>
                      </button>
                      <button
                        onClick={deleteAudio}
                        className="px-3 py-2 rounded-md bg-slate-700/50 text-purple-100 flex items-center gap-2 border border-purple-500/30 hover:bg-slate-700"
                        aria-label={t('actions.delete')}
                      >
                        <Trash2 size={18} />
                        <span className="hidden sm:inline">{t('actions.delete')}</span>
                        <span className="sr-only">{t('actions.delete')}</span>
                      </button>
                    </div>
                  )}
                </div>

                <div>
                  <div className="text-sm text-purple-300 mb-1">{t('labels.text')}</div>
                  <textarea
                    value={currentText}
                    onChange={(e) => setCurrentText(e.target.value)}
                    rows={6}
                    className="w-full bg-slate-700/50 text-purple-100 rounded-md p-3 border border-purple-500/30"
                    placeholder={t('placeholders.record_or_type')}
                  />
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={saveEntry}
                    disabled={isProcessing || !currentText.trim()}
                    className="px-4 py-2 rounded-md bg-gradient-to-r from-purple-600 to-pink-600 text-white flex items-center gap-2 hover:from-purple-700 hover:to-pink-700 disabled:opacity-50"
                  >
                    <Save size={18} /> <span>{isProcessing ? t('actions.saving') : t('actions.save')}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {reviewModal.visible && (
        <div className="fixed inset-0 bg-black bg-opacity-80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 z-50">
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl max-w-md w-full border border-purple-500/30 shadow-2xl">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl sm:text-2xl font-bold text-purple-200">{t('modals.review_title')}</h2>
                <button onClick={closeReviewModal} className="text-purple-400 hover:text-purple-300"><X size={24} /></button>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-purple-300 mb-1">{t('modals.original_text')}</div>
                  <div className="text-purple-100 bg-slate-700/50 rounded-md p-3">{reviewModal.data?.original}</div>
                </div>
                {reviewModal.data?.audioUri && (
                  <div className="mt-2 mb-4">
                    <audio controls src={reviewModal.data.audioUri} className="w-full audio-compact" />
                  </div>
                )}
                <div className="mt-4 pt-4 border-t border-slate-700/60">
                    <div className="flex items-center gap-3 mb-1">
                      <div className="text-sm text-purple-300">{t('modals.corrected_text')}</div>
                      <button
                        type="button"
                        onClick={() => {
                          const text = reviewModal.data?.correctedText || reviewModal.data?.original || '';
                          if (!text) return;
                          const lang = reviewModal.data?.language || selectedLanguage;
                          speakText(text, lang);
                        }}
                        className="hidden"
                      >
                        <Play size={16} /> {t('tts.speak_browser')}
                      </button>
                      {reviewModal.data?.explanationsHtml && (
                        <button
                          type="button"
                          onClick={(e) => { e.stopPropagation(); openExplainModal(reviewModal.data.explanationsHtml); }}
                          className="ml-auto inline-flex items-center justify-center px-2.5 py-1 rounded-md bg-purple-600 text-white text-sm hover:bg-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-400 shadow-sm"
                          aria-label={t('modals.open_explanations_aria')}
                        >
                          {t('modals.explanations')}
                        </button>
                      )}
                    </div>
                  <div className="corrected-text text-purple-100 bg-slate-700/50 rounded-md p-3" dangerouslySetInnerHTML={{ __html: reviewModal.data?.correctedHtml || '' }} />
                  {reviewModal.data?.ttsUri && (
                    <div className="mt-3 border-t border-slate-700/60">
                      <audio controls src={reviewModal.data.ttsUri} className="w-full audio-compact" />
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {audioModal.visible && (
        <div className="fixed inset-0 bg-black bg-opacity-80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 z-[60]">
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl max-w-md w-full border border-purple-500/30 shadow-2xl" role="dialog" aria-modal="true">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl sm:text-2xl font-bold text-purple-200">{audioModal.title || t('modals.tts_title')}</h2>
                <button onClick={closeAudioModal} className="text-purple-400 hover:text-purple-300"><X size={24} /></button>
              </div>
              <audio controls src={audioModal.src || ''} className="w-full" />
            </div>
          </div>
        </div>
      )}

      {settingsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 z-[70]">
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl max-w-md w-full border border-purple-500/30 shadow-2xl">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl sm:text-2xl font-bold text-purple-200">{t('modals.ui_language_title')}</h2>
                <button onClick={() => setSettingsModal(false)} className="text-purple-400 hover:text-purple-300"><X size={24} /></button>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-purple-300 mb-2">{t('modals.select_language')}</div>
                  <div className="space-y-2">
                    {[{ code: 'en', name: 'English', flagSrc: '/flags/us.svg' }, { code: 'ru', name: 'Русский', flagSrc: '/flags/ru.svg' }, { code: 'pl', name: 'Polski', flagSrc: '/flags/pl.svg' }, { code: 'es', name: 'Español', flagSrc: '/flags/es.svg' }, { code: 'pt', name: 'Português', flagSrc: '/flags/pt.svg' }].map((l) => (
                      <label key={l.code} className="flex items-center gap-3 p-2 rounded-md bg-slate-700/40 border border-purple-500/30 hover:bg-slate-700/60 cursor-pointer">
                        <input
                          type="radio"
                          name="uiLang"
                          className="accent-purple-500"
                          checked={pendingLang === l.code}
                          onChange={() => setPendingLang(l.code)}
                        />
                        <img src={l.flagSrc} alt={l.name} className="h-4 w-6 rounded-sm border border-purple-500/30" />
                        <span className="text-purple-200">{l.name}</span>
                      </label>
                    ))}
                  </div>
                </div>
                <div className="flex justify-end gap-3">
                  <button
                    onClick={() => setSettingsModal(false)}
                    className="px-4 py-2 rounded-md bg-slate-700/50 text-purple-100 border border-purple-500/30 hover:bg-slate-700"
                  >
                    {t('modals.close')}
                  </button>
                  <button
                    onClick={() => { setLang(pendingLang); setSettingsModal(false); }}
                    className="px-4 py-2 rounded-md bg-gradient-to-r from-purple-600 to-pink-600 text-white border border-purple-500/40 hover:from-purple-700 hover:to-pink-700"
                  >
                    {t('modals.apply')}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {explainModal.visible && (
        <div className="fixed inset-0 bg-black bg-opacity-80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 z-[60]">
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl max-w-md w-full border border-purple-500/30 shadow-2xl" role="dialog" aria-modal="true">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl sm:text-2xl font-bold text-purple-200">{t('modals.explanations')}</h2>
                <button onClick={closeExplainModal} className="text-purple-400 hover:text-purple-300"><X size={24} /></button>
              </div>
              <div className="prose prose-invert max-w-none">
                <div className="text-purple-100" dangerouslySetInnerHTML={{ __html: explainModal.html || '' }} />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DiaryApp;