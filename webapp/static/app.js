let mediaStream = null;
let mediaRecorder = null;
let recordedChunks = [];

const modal = document.getElementById('modal');
const btnCreate = document.getElementById('btnCreate');
const btnRecord = document.getElementById('btnRecord');
const btnStop = document.getElementById('btnStop');
const btnTranscribe = document.getElementById('btnTranscribe');
const btnSave = document.getElementById('btnSave');
const modalClose = document.getElementById('modalClose');
const statusEl = document.getElementById('status');
const textEl = document.getElementById('text');
const entriesEl = document.getElementById('entries');

function openModal(prefillText = '') {
  textEl.value = prefillText || '';
  modal.classList.remove('hidden');
}
function closeModal() {
  modal.classList.add('hidden');
}

btnCreate.addEventListener('click', () => openModal());
modalClose.addEventListener('click', closeModal);

async function fetchEntries() {
  const resp = await fetch('/api/entries');
  const data = await resp.json();
  const items = data.items || [];
  renderEntries(items);
}

function groupByDate(items) {
  const groups = {};
  for (const it of items) {
    const d = (it.created_at || '').slice(0, 10); // YYYY-MM-DD
    if (!groups[d]) groups[d] = [];
    groups[d].push(it);
  }
  return groups;
}

function renderEntries(items) {
  const groups = groupByDate(items);
  const dates = Object.keys(groups).sort((a,b) => b.localeCompare(a));
  entriesEl.innerHTML = '';
  for (const date of dates) {
    const grp = document.createElement('div');
    grp.className = 'entry-group';
    const h = document.createElement('h3');
    h.textContent = date;
    grp.appendChild(h);
    for (const it of groups[date]) {
      const card = document.createElement('div');
      card.className = 'entry';
      card.addEventListener('click', () => openModal(it.text || ''));
      const meta = document.createElement('div');
      meta.className = 'meta';
      meta.textContent = `#${it.id} • ${(it.created_at || '').slice(11, 19)}`;
      const txt = document.createElement('div');
      txt.className = 'text';
      txt.textContent = it.text || '';
      card.appendChild(meta);
      card.appendChild(txt);
      grp.appendChild(card);
    }
    entriesEl.appendChild(grp);
  }
}

async function startRecording() {
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recordedChunks = [];
    mediaRecorder = new MediaRecorder(mediaStream, { mimeType: 'audio/webm' });
    mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) recordedChunks.push(e.data); };
    mediaRecorder.onstop = () => { statusEl.textContent = 'Запись остановлена'; };
    mediaRecorder.start();
    btnRecord.disabled = true;
    btnStop.disabled = false;
    statusEl.textContent = 'Идет запись...';
  } catch (err) {
    console.error(err);
    statusEl.textContent = 'Не удалось получить доступ к микрофону';
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
  if (mediaStream) {
    mediaStream.getTracks().forEach(t => t.stop());
  }
  btnRecord.disabled = false;
  btnStop.disabled = true;
}

btnRecord.addEventListener('click', startRecording);
btnStop.addEventListener('click', stopRecording);

async function transcribe() {
  if (!recordedChunks.length) {
    statusEl.textContent = 'Нет аудио для транскрибации';
    return;
  }
  const blob = new Blob(recordedChunks, { type: 'audio/webm' });
  const form = new FormData();
  const filename = `record_${Date.now()}.webm`;
  form.append('audio', blob, filename);
  statusEl.textContent = 'Отправка аудио...';
  const resp = await fetch('/api/transcribe', { method: 'POST', body: form });
  const data = await resp.json();
  textEl.value = data.text || '';
  statusEl.textContent = 'Транскрибировано';
}

btnTranscribe.addEventListener('click', transcribe);

async function saveEntry() {
  const text = textEl.value.trim();
  if (!text) { statusEl.textContent = 'Пустой текст'; return; }
  const resp = await fetch('/api/entries', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!resp.ok) {
    statusEl.textContent = 'Ошибка сохранения';
    return;
  }
  statusEl.textContent = 'Сохранено';
  closeModal();
  await fetchEntries();
}

btnSave.addEventListener('click', saveEntry);

// Init
fetchEntries();