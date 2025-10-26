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
  
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const audioRef = useRef(null);
  const streamRef = useRef(null);

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
      const serverEntries = (data.entries || []).map(e => ({
        id: e.id,
        text: e.text,
        timestamp: e.timestamp,
        language: e.language,
        duration: e.audio_duration,
        isOffline: false
      }));
      const offlineEntries = getOfflineEntries();
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
        const normalized = {
          id: saved.id,
          text: saved.text,
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
      const normalized = {
        id: saved.id,
        text: saved.text,
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
      // Fallback: save offline
      const offlineEntry = {
        tempId: `offline_${Date.now()}`,
        id: `offline_${Date.now()}`,
        text: currentText.trim(),
        timestamp,
        language: selectedLanguage,
        duration: recordingTime,
        isOffline: true
      };
      const offlineEntries = getOfflineEntries();
      setOfflineEntries([offlineEntry, ...offlineEntries]);
      setEntries(prev => [offlineEntry, ...prev]);
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
    { code: 'ru-RU', name: 'Русский' },
    { code: 'en-US', name: 'English' },
    { code: 'pt-BR', name: 'Português' },
    { code: 'es-ES', name: 'Español' },
    { code: 'pl-PL', name: 'Polski' }
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
                          {entry.duration && (
                            <div className="text-xs text-purple-400/40">
                              {formatTime(entry.duration)}
                            </div>
                          )}
                        </div>
                        <div className="text-purple-100 leading-relaxed">{entry.text}</div>
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
                <button
                  onClick={() => {
                    stopRecording();
                    deleteAudio();
                    setShowModal(false);
                  }}
                  className="text-purple-400 hover:text-purple-300"
                >
                  <X size={24} />
                </button>
              </div>

              <div className="mb-4">
                <label className="text-purple-300 text-sm mb-2 block">Язык</label>
                <select
                  value={selectedLanguage}
                  onChange={(e) => setSelectedLanguage(e.target.value)}
                  disabled={isRecording || audioBlob}
                  className="w-full bg-slate-700 text-purple-100 rounded-lg px-4 py-2 border border-purple-500/30 focus:outline-none focus:border-purple-500 disabled:opacity-50"
                >
                  {languages.map(lang => (
                    <option key={lang.code} value={lang.code}>{lang.name}</option>
                  ))}
                </select>
              </div>

              <div className="flex justify-center items-center gap-4 mb-6">
                {!audioBlob ? (
                  <button
                    onClick={isRecording ? stopRecording : startRecording}
                    disabled={isProcessing}
                    className={`w-24 h-24 rounded-full flex items-center justify-center transition-all shadow-lg ${
                      isRecording
                        ? 'bg-red-500 hover:bg-red-600 shadow-red-500/50'
                        : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 shadow-purple-500/50'
                    } disabled:opacity-50`}
                  >
                    {isRecording ? <Square size={40} className="text-white" /> : <Mic size={40} className="text-white" />}
                  </button>
                ) : (
                  <>
                    <button
                      onClick={playAudio}
                      disabled={isPlaying}
                      className="w-16 h-16 rounded-full bg-green-600 hover:bg-green-700 flex items-center justify-center shadow-lg disabled:opacity-50"
                    >
                      <Play size={28} className="text-white ml-1" />
                    </button>
                    <button
                      onClick={deleteAudio}
                      className="w-16 h-16 rounded-full bg-red-600 hover:bg-red-700 flex items-center justify-center shadow-lg"
                    >
                      <Trash2 size={28} className="text-white" />
                    </button>
                  </>
                )}
              </div>

              {(isRecording || recordingTime > 0) && (
                <div className="text-center mb-4">
                  <div className={`text-2xl font-mono ${isRecording ? 'text-red-400 animate-pulse' : 'text-purple-300'}`}>
                    {formatTime(recordingTime)}
                  </div>
                  {isRecording && (
                    <div className="text-sm text-purple-400 mt-1">Идет запись...</div>
                  )}
                </div>
              )}

              {isProcessing && (
                <div className="text-center text-purple-300 mb-4">
                  <div className="animate-spin inline-block w-6 h-6 border-4 border-purple-500 border-t-transparent rounded-full mb-2"></div>
                  <div>Обработка...</div>
                </div>
              )}

              <textarea
                value={currentText}
                onChange={(e) => setCurrentText(e.target.value)}
                placeholder="Транскрибированный текст появится здесь..."
                disabled={isProcessing}
                className="w-full bg-slate-700 text-purple-100 rounded-lg p-4 border border-purple-500/30 focus:outline-none focus:border-purple-500 min-h-32 mb-4 disabled:opacity-50"
              />

              <button
                onClick={saveEntry}
                disabled={!currentText.trim() || isProcessing}
                className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:from-gray-600 disabled:to-gray-700 text-white rounded-xl py-3 px-6 flex items-center justify-center gap-2 transition-all shadow-lg disabled:opacity-50"
              >
                <Save size={20} />
                <span className="font-semibold">
                  {isProcessing ? 'Сохранение...' : 'Сохранить'}
                </span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DiaryApp;