# app.py - Синхронная версия с Flask
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv
from groq import Groq
import threading
import tempfile
import subprocess
import re
import json
try:
    import google.generativeai as genai
except Exception:
    genai = None

# Gemini API key configuration
load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY') or os.getenv('GENAI_API_KEY')
if genai and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("[REVIEW] Gemini configured")
    except Exception as _cfg_err:
        print(f"[REVIEW] Gemini configure error: {_cfg_err}")
else:
    print("[REVIEW] WARNING: Gemini API key not found or library unavailable. /api/review will operate in fallback mode.")

# Flask - создаем приложение
app = Flask(__name__)

# Настраиваем CORS
CORS(app, origins="*")

# Устанавливаем конфигурацию
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///diary.db')
# PostgreSQL: postgresql://user:pass@host/db

# SQLAlchemy
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Groq client
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

# SQLAlchemy Models
Base = declarative_base()

class Entry(Base):
    __tablename__ = 'entry'
    
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    language = Column(String(10), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    audio_duration = Column(Float, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'language': self.language,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'audio_duration': self.audio_duration
        }

# Create tables
Base.metadata.create_all(bind=engine)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    try:
        print(f"[TRANSCRIBE] Request received - Files: {list(request.files.keys())}")
        print(f"[TRANSCRIBE] Form data: {dict(request.form)}")
        
        if 'audio' not in request.files:
            print("[TRANSCRIBE] ERROR: No audio file in request")
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        language = request.form.get('language', 'auto')
        
        # Read size for logging and reset pointer on underlying stream
        raw_preview = audio_file.stream.read()
        print(f"[TRANSCRIBE] Audio file: {audio_file.filename}, size: {len(raw_preview)} bytes, content_type: {audio_file.content_type}")
        audio_file.stream.seek(0)
        
        if audio_file.filename == '':
            print("[TRANSCRIBE] ERROR: Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        # Ensure GROQ_API_KEY is present
        api_key_present = bool(os.getenv('GROQ_API_KEY'))
        print(f"[TRANSCRIBE] GROQ_API_KEY present: {api_key_present}")
        
        print(f"[TRANSCRIBE] Starting Groq transcription with language: {language}")
        
        # Write to a temporary file with correct extension for Groq
        ext = os.path.splitext(audio_file.filename)[1] or '.webm'
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(raw_preview)
            tmp_path = tmp.name
        print(f"[TRANSCRIBE] Temp file created: {tmp_path}")
        
        # Convert webm/opus to wav 16k mono if needed
        use_path = tmp_path
        converted_path = None
        try:
            if (ext.lower() == '.webm') or (audio_file.content_type and 'webm' in audio_file.content_type):
                converted_path = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
                cmd = ['ffmpeg', '-y', '-i', tmp_path, '-ac', '1', '-ar', '16000', converted_path]
                print(f"[TRANSCRIBE] Converting webm→wav: {' '.join(cmd)}")
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if res.returncode != 0:
                    print(f"[TRANSCRIBE] ffmpeg error: {res.stderr}")
                else:
                    use_path = converted_path
                    print(f"[TRANSCRIBE] Conversion OK: {converted_path}")
        except Exception as conv_err:
            print(f"[TRANSCRIBE] ffmpeg exception: {conv_err}")
        
        try:
            with open(use_path, 'rb') as f:
                transcription = groq_client.audio.transcriptions.create(
                    file=f,
                    model="whisper-large-v3",
                    language=language if language != 'auto' else None
                )
        finally:
            # Clean temp files
            for p in [tmp_path, converted_path]:
                if p:
                    try:
                        os.remove(p)
                        print(f"[TRANSCRIBE] Temp file removed: {p}")
                    except Exception as cleanup_err:
                        print(f"[TRANSCRIBE] Temp file cleanup error: {cleanup_err}")
        
        print(f"[TRANSCRIBE] Success! Text length: {len(transcription.text)} chars")
        
        return jsonify({
            'text': transcription.text,
            'language': language
        })
        
    except Exception as e:
        print(f"[TRANSCRIBE] ERROR: {str(e)}")
        import traceback
        print(f"[TRANSCRIBE] Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/entries', methods=['GET'])
def get_entries():
    try:
        db = SessionLocal()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        language = request.args.get('language')
        
        query = db.query(Entry)
        
        if language:
            query = query.filter(Entry.language == language)
        
        # Pagination
        offset = (page - 1) * per_page
        entries = query.order_by(Entry.timestamp.desc()).offset(offset).limit(per_page).all()
        total = query.count()
        
        return jsonify({
            'entries': [entry.to_dict() for entry in entries],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/entries', methods=['POST'])
def create_entry():
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Text is required'}), 400
        
        db = SessionLocal()
        entry = Entry(
            text=data['text'],
            language=data.get('language', 'unknown'),
            audio_duration=data.get('audio_duration')
        )
        
        db.add(entry)
        db.commit()
        db.refresh(entry)
        
        return jsonify(entry.to_dict()), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/entries/<int:entry_id>', methods=['GET'])
def get_entry(entry_id):
    try:
        db = SessionLocal()
        entry = db.query(Entry).filter(Entry.id == entry_id).first()
        
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
        
        return jsonify(entry.to_dict())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/entries/<int:entry_id>', methods=['PUT'])
def update_entry(entry_id):
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        db = SessionLocal()
        entry = db.query(Entry).filter(Entry.id == entry_id).first()
        
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
        
        if 'text' in data:
            entry.text = data['text']
        if 'language' in data:
            entry.language = data['language']
        if 'audio_duration' in data:
            entry.audio_duration = data['audio_duration']
        
        db.commit()
        db.refresh(entry)
        
        return jsonify(entry.to_dict())
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/entries/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    try:
        db = SessionLocal()
        entry = db.query(Entry).filter(Entry.id == entry_id).first()
        
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
        
        db.delete(entry)
        db.commit()
        
        return jsonify({'message': 'Entry deleted successfully'})
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/search', methods=['GET'])
def search_entries():
    try:
        query_text = request.args.get('q', '').strip()
        
        if not query_text:
            return jsonify({'error': 'Search query is required'}), 400
        
        db = SessionLocal()
        entries = db.query(Entry).filter(
            Entry.text.contains(query_text)
        ).order_by(Entry.timestamp.desc()).limit(50).all()
        
        return jsonify({
            'entries': [entry.to_dict() for entry in entries],
            'query': query_text,
            'count': len(entries)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/review', methods=['POST'])
def review_entry():
    try:
        payload = request.get_json()
        if not payload or 'text' not in payload:
            return jsonify({'error': 'Text is required'}), 400
        text = payload['text']
        language = payload.get('language', 'unknown')

        result = review_with_gemini(text, language)
        corrected = result.get('corrected_text', text)
        is_changed = bool(result.get('changed', corrected.strip() != text.strip()))
        corrected_html = _highlight_diff(text, corrected) if is_changed else corrected
        explanations = result.get('explanations', [])
        explanations_html = '<br>'.join(explanations) if explanations else ''

        return jsonify({
            'original_text': text,
            'corrected_text': corrected,
            'corrected_html': corrected_html,
            'explanations': explanations,
            'explanations_html': explanations_html,
            'is_changed': is_changed,
            'language': result.get('language', language)
        })
    except Exception as e:
        print(f"[REVIEW] ERROR: {e}")
        return jsonify({'error': str(e)}), 500

# Helper functions for diff/highlight
import difflib

def _tokenize(text: str):
    return re.findall(r"\w+|[^\w\s]", text, re.UNICODE)


def _rebuild_with_spaces(tokens):
    res = []
    for i, t in enumerate(tokens):
        res.append(t)
        if i < len(tokens) - 1:
            curr_is_word = bool(re.match(r"\w", t, re.UNICODE))
            next_is_word = bool(re.match(r"\w", tokens[i + 1], re.UNICODE))
            if curr_is_word and next_is_word:
                res.append(' ')
            elif t in ['"', "'"] and next_is_word:
                res.append(' ')
            elif curr_is_word and tokens[i + 1] in ['"', "'"]:
                res.append(' ')
    return ''.join(res)


def _highlight_diff(original: str, corrected: str) -> str:
    orig_tokens = _tokenize(original)
    corr_tokens = _tokenize(corrected)
    sm = difflib.SequenceMatcher(a=orig_tokens, b=corr_tokens)
    parts = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        segment = corr_tokens[j1:j2]
        if tag == 'equal':
            parts.append(_rebuild_with_spaces(segment))
        elif tag in ('replace', 'insert'):
            if segment:
                parts.append('<mark>' + _rebuild_with_spaces(segment) + '</mark>')
        # delete: skip
    return ''.join(parts)


def _build_review_prompt(text: str, language: str):
    lang_label = language or 'auto-detected language'
    return (
        "You are an expert language tutor. Check the phrase for grammatical and semantic correctness while preserving its original meaning. "
        "If corrections are needed, provide the corrected version. Respond in pure JSON with keys: "
        "corrected_text (string), explanations (array of strings), language (string), changed (boolean). "
        "Only output JSON without markdown or code fences. "
        f"Language: {lang_label}. Phrase: \"\"\"{text}\"\"\""
    )


def review_with_gemini(text: str, language: str):
    if not (genai and GEMINI_API_KEY):
        return {
            'corrected_text': text,
            'explanations': ['Проверка недоступна: отсутствует ключ Gemini или библиотека.'],
            'language': language,
            'changed': False
        }
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        resp = model.generate_content(_build_review_prompt(text, language))
        raw = (resp.text or '').strip()
        # Try to extract JSON
        start = raw.find('{')
        end = raw.rfind('}')
        if start != -1 and end != -1:
            raw = raw[start:end + 1]
        data = json.loads(raw)
        corrected = data.get('corrected_text') or text
        explanations = data.get('explanations') or []
        changed = data.get('changed')
        if changed is None:
            changed = corrected.strip() != text.strip()
        return {
            'corrected_text': corrected,
            'explanations': explanations,
            'language': data.get('language') or language,
            'changed': bool(changed)
        }
    except Exception as e:
        print(f"[REVIEW] Gemini error: {e}")
        return {
            'corrected_text': text,
            'explanations': ['Не удалось выполнить проверку, используем исходный текст.'],
            'language': language,
            'changed': False
        }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)