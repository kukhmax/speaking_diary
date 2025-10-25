# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv
import openai
from groq import Groq
import base64

load_dotenv()

app = Flask(__name__)
CORS(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///diary.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)

# Groq Client for Whisper API (Free tier available)
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

# Models
class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    audio_duration = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'language': self.language,
            'timestamp': self.timestamp.isoformat(),
            'audio_duration': self.audio_duration
        }

# Initialize database
with app.app_context():
    db.create_all()

# Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Server is running'})

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Transcribe audio file using Groq Whisper API
    Expects: audio file in form-data with key 'audio'
    Optional: language code
    """
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        language = request.form.get('language', 'ru')
        
        # Map language codes
        lang_map = {
            'ru-RU': 'ru',
            'en-US': 'en',
            'pt-BR': 'pt',
            'es-ES': 'es',
            'pl-PL': 'pl'
        }
        language_code = lang_map.get(language, language.split('-')[0])
        
        # Transcribe using Groq Whisper
        transcription = groq_client.audio.transcriptions.create(
            file=(audio_file.filename, audio_file.read()),
            model="whisper-large-v3",
            language=language_code,
            response_format="json"
        )
        
        return jsonify({
            'text': transcription.text,
            'language': language_code
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/entries', methods=['GET'])
def get_entries():
    """Get all entries, optionally filtered by date range"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Entry.query
        
        if start_date:
            query = query.filter(Entry.timestamp >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(Entry.timestamp <= datetime.fromisoformat(end_date))
        
        entries = query.order_by(Entry.timestamp.desc()).all()
        return jsonify([entry.to_dict() for entry in entries])
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/entries', methods=['POST'])
def create_entry():
    """Create a new diary entry"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Text is required'}), 400
        
        entry = Entry(
            text=data['text'],
            language=data.get('language', 'ru-RU'),
            audio_duration=data.get('audio_duration')
        )
        
        db.session.add(entry)
        db.session.commit()
        
        return jsonify(entry.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/entries/<int:entry_id>', methods=['GET'])
def get_entry(entry_id):
    """Get a specific entry"""
    try:
        entry = Entry.query.get_or_404(entry_id)
        return jsonify(entry.to_dict())
    
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/entries/<int:entry_id>', methods=['PUT'])
def update_entry(entry_id):
    """Update an existing entry"""
    try:
        entry = Entry.query.get_or_404(entry_id)
        data = request.get_json()
        
        if 'text' in data:
            entry.text = data['text']
        if 'language' in data:
            entry.language = data['language']
        
        db.session.commit()
        return jsonify(entry.to_dict())
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/entries/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    """Delete an entry"""
    try:
        entry = Entry.query.get_or_404(entry_id)
        db.session.delete(entry)
        db.session.commit()
        return jsonify({'message': 'Entry deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_entries():
    """Search entries by text content"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify([])
        
        entries = Entry.query.filter(
            Entry.text.ilike(f'%{query}%')
        ).order_by(Entry.timestamp.desc()).all()
        
        return jsonify([entry.to_dict() for entry in entries])
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)