import React, { useState, useEffect, useRef } from 'react';
import { Mic, Save, X, Plus, ChevronDown, ChevronRight, Square, Play, Trash2 } from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const DiaryApp = () => {
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
  const UI_LANGUAGE = 'ru';
  
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const audioRef = useRef(null);
  const streamRef = useRef(null);

  // Review & Audio storage helpers
  const REVIEW_PREFIX = 'entry_review:';
  const AUDIO_PREFIX = 'entry_audio:';
  const saveReview = (id, obj) => { try { localStorage.setItem(REVIEW_PREFIX + id, JSON.stringify(obj)); } catch {} };
  const loadReview = (id) => { try { const s = localStorage.getItem(REVIEW_PREFIX + id); return s ? JSON.parse(s) : null; } catch { return null; } };
  const blobToDataUrl = (blob) => new Promise((resolve, reject) => { const r = new FileReader(); r.onloadend = () => resolve(r.result); r.onerror = reject; r.readAsDataURL(blob); });
  const saveAudio = async (id, blob) => { try { const url = await blobToDataUrl(blob); localStorage.setItem(AUDIO_PREFIX + id, url); } catch {} };
  const loadAudio = (id) => { try { return localStorage.getItem(AUDIO_PREFIX + id); } catch { return null; } };
  const fixHtmlSpaces = (html) => {
    if (!html) return html;
    try {
      return html
        .replace(/([\p{L}\p{N}])<mark/gu, '$1 <mark')
        .replace(/<\/mark>([\p{L}\p{N}])/gu, '</mark> $1');
    } catch {
      return html;
    }
  };
  const removeReview = (id) => { try { localStorage.removeItem(REVIEW_PREFIX + id); } catch {} };
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
    const byName = voices.find(v => /ru|russian|русский|pt|portuguese|português|es|spanish|español|pl|polish|polski/i.test(v.name || ''));
    return byName || null;
  };
  const speakText = async (text, lang) => {
    const useLang = normalizeSpeechLang(lang);
    const utter = new SpeechSynthesisUtterance(text);
    try {
      const voices = await ensureVoices();
      const v = pickVoice(voices, useLang);
      if (v) {
        utter.voice = v;
        utter.lang = v.lang || useLang;
      } else {
        // Fallback: не блокировать воспроизведение, используем системный голос
        utter.lang = 'en-US';
      }
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utter);
    } catch (e) {
      console.error('TTS error:', e);
      window.speechSynthesis.cancel();
      utter.lang = 'en-US';
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
      const resp = await fetch(`${API_BASE}/entries/${entry.id}`, { method: 'DELETE' });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      removeReview(entry.id);
      removeAudio(entry.id);
      setEntries(prev => prev.filter(e => e.id !== entry.id));
    } catch (err) {
      console.error('Delete entry failed:', err);
      alert('Не удалось удалить запись. Проверьте соединение.');
    }
  };
  const migrateLocalData = (oldId, newId) => { try { const r = loadReview(oldId); if (r) saveReview(newId, r); const a = loadAudio(oldId); if (a) localStorage.setItem(AUDIO_PREFIX + newId, a); localStorage.removeItem(REVIEW_PREFIX + oldId); localStorage.removeItem(AUDIO_PREFIX + oldId); } catch {} };

  const openReview = (entry) => {
    const rev = loadReview(entry.id);
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
  };
  const closeReviewModal = () => setReviewModal({ visible: false, data: null });

  useEffect(() => {
    loadEntries();
    return () => {
      stopRecording();
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

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
      const response = await fetch(`${API_BASE}/entries?per_page=50`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      const serverEntries = (data.entries || []).map(e => {
        const rev = loadReview(e.id);
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
        const rev = loadReview(e.id);
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
        const response = await fetch(`${API_BASE}/entries`, {
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
          const revResp = await fetch(`${API_BASE}/review`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: saved.text, language: saved.language, ui_language: UI_LANGUAGE })
          });
          if (revResp.ok) {
            const revObj = await revResp.json();
            saveReview(saved.id, { ...revObj, original_text: saved.text });
          }
        } catch (e) {
          console.error('Review failed during sync:', e);
        }
        const rev = loadReview(saved.id);
        const normalized = {
          id: saved.id,
          text: saved.text,
          textHtml: rev?.corrected_html || null,
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
      alert('Не удалось получить доступ к микрофону. Проверьте разрешения.');
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
    setCurrentText('Транскрибация...');

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
      
      const response = await fetch(`${API_BASE}/transcribe`, {
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
      
      setCurrentText(data.text || 'Транскрибация не удалась');
      setIsProcessing(false);

    } catch (error) {
      console.error('Transcription error:', error);
      setCurrentText(`Ошибка транскрибации: ${error.message}. Проверьте подключение к backend и настройки Groq API.`);
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
      const response = await fetch(`${API_BASE}/entries`, {
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
        const revResp = await fetch(`${API_BASE}/review`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: saved.text, language: saved.language, ui_language: UI_LANGUAGE })
        });
        if (revResp.ok) {
          const rev = await revResp.json();
          saveReview(saved.id, { ...rev, original_text: saved.text });
        }
      } catch (e) {
        console.error('Review request failed:', e);
      }

      // Сохраняем аудио локально под id записи
      if (audioBlob) {
        try { await saveAudio(saved.id, audioBlob); } catch {}
      }

      const rev = loadReview(saved.id);
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
      alert('Сохранено офлайн. Запись синхронизируется при восстановлении соединения.');
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
      const date = new Date(entry.timestamp).toLocaleDateString('ru-RU', {
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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="bg-black bg-opacity-30 backdrop-blur-md border-b border-purple-500/20">
        <div className="max-w-2xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
            Дневник
          </h1>
          <p className="text-purple-300/70 text-sm mt-1">Голосовые заметки с MediaRecorder</p>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6">
        <button
          onClick={() => setShowModal(true)}
          className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-2xl py-4 px-6 flex items-center justify-center gap-3 shadow-lg shadow-purple-500/30 transition-all mb-6"
        >
          <Plus size={24} />
          <span className="text-lg font-semibold">Создать запись</span>
        </button>

        <div className="space-y-3">
          {Object.keys(groupedEntries).length === 0 ? (
            <div className="text-center py-12 text-purple-300/50">
              <p>Пока нет записей</p>
              <p className="text-sm mt-2">Нажмите "Создать запись" чтобы начать</p>
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
                              {new Date(entry.timestamp).toLocaleTimeString('ru-RU', {
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </div>
                            {entry.isOffline && (
                              <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-300 border border-yellow-500/30">
                                Офлайн
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
                              aria-label="Удалить запись"
                            >
                              <X size={18} />
                            </button>
                          </div>
                        </div>
                        <div className="flex items-start gap-2">
                          <img src={getFlagSrc(entry.language)} alt={entry.language} className="h-4 w-6 rounded-sm border border-purple-500/30 mt-1" />
                          {entry.textHtml ? (
                            <div
                              className="text-purple-100 leading-relaxed cursor-pointer"
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
        <div className="fixed inset-0 bg-black bg-opacity-80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl max-w-md w-full border border-purple-500/30 shadow-2xl">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-purple-200">Новая запись</h2>
                <button onClick={() => setShowModal(false)} className="text-purple-400 hover:text-purple-300"><X size={24} /></button>
              </div>

              <div className="space-y-4">
                <div>
                  <div className="text-sm text-purple-300 mb-1">Язык</div>
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

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {isRecording ? (
                      <button
                        onClick={stopRecording}
                        className="px-4 py-2 rounded-md bg-red-600 text-white flex items-center gap-2 hover:bg-red-700"
                      >
                        <Square size={18} /> Остановить
                      </button>
                    ) : (
                      <button
                        onClick={startRecording}
                        className="px-4 py-2 rounded-md bg-purple-600 text-white flex items-center gap-2 hover:bg-purple-700"
                      >
                        <Mic size={18} /> Запись
                      </button>
                    )}
                    <span className="text-purple-300">{formatTime(recordingTime)}</span>
                  </div>

                  {audioBlob && (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={playAudio}
                        className="px-3 py-2 rounded-md bg-slate-700/50 text-purple-100 flex items-center gap-2 border border-purple-500/30 hover:bg-slate-700"
                      >
                        <Play size={18} /> Прослушать
                      </button>
                      <button
                        onClick={deleteAudio}
                        className="px-3 py-2 rounded-md bg-slate-700/50 text-purple-100 flex items-center gap-2 border border-purple-500/30 hover:bg-slate-700"
                      >
                        <Trash2 size={18} /> Удалить
                      </button>
                    </div>
                  )}
                </div>

                <div>
                  <div className="text-sm text-purple-300 mb-1">Текст</div>
                  <textarea
                    value={currentText}
                    onChange={(e) => setCurrentText(e.target.value)}
                    rows={6}
                    className="w-full bg-slate-700/50 text-purple-100 rounded-md p-3 border border-purple-500/30"
                    placeholder="Скажите что-нибудь или введите текст вручную..."
                  />
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={saveEntry}
                    disabled={isProcessing || !currentText.trim()}
                    className="px-4 py-2 rounded-md bg-gradient-to-r from-purple-600 to-pink-600 text-white flex items-center gap-2 hover:from-purple-700 hover:to-pink-700 disabled:opacity-50"
                  >
                    <Save size={18} /> {isProcessing ? 'Сохранение...' : 'Сохранить'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {reviewModal.visible && (
        <div className="fixed inset-0 bg-black bg-opacity-80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl max-w-md w-full border border-purple-500/30 shadow-2xl">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-purple-200">Проверка и исправления</h2>
                <button onClick={closeReviewModal} className="text-purple-400 hover:text-purple-300"><X size={24} /></button>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-purple-300 mb-1">Исходный текст</div>
                  <div className="text-purple-100 bg-slate-700/50 rounded-md p-3">{reviewModal.data?.original}</div>
                </div>
                {reviewModal.data?.audioUri && (
                  <div>
                    <div className="text-sm text-purple-300 mb-1">Аудио</div>
                    <audio controls src={reviewModal.data.audioUri} className="w-full" />
                  </div>
                )}
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <div className="text-sm text-purple-300">Исправленный текст</div>
                    {!reviewModal.data?.ttsUri && (
                      <button onClick={() => {
                      const text = reviewModal.data?.correctedText || reviewModal.data?.original || '';
                      if (!text) return;
                      const lang = reviewModal.data?.language || selectedLanguage;
                      speakText(text, lang);
                      }} className="text-purple-300 hover:text-purple-200 flex items-center gap-1">
                        <Play size={16} /> Озвучить (браузер)
                      </button>
                    )}
                  </div>
                  {reviewModal.data?.ttsUri && (
                    <div className="mb-2">
                      <div className="text-sm text-purple-300 mb-1">Озвучка (синтез на сервере)</div>
                      <audio controls src={reviewModal.data.ttsUri} className="w-full" />
                    </div>
                  )}
                  <div className="text-purple-100 bg-slate-700/50 rounded-md p-3" dangerouslySetInnerHTML={{ __html: reviewModal.data?.correctedHtml || '' }} />
                </div>
                {reviewModal.data?.explanationsHtml && (
                  <div>
                    <div className="text-sm text-purple-300 mb-1">Пояснения</div>
                    <div className="prose prose-invert max-w-none">
                      <div className="text-purple-100" dangerouslySetInnerHTML={{ __html: reviewModal.data.explanationsHtml }} />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DiaryApp;