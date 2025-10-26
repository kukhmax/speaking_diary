# app.py - Асинхронная версия с Groq 0.33.0
from quart import Quart, request, jsonify
from quart_cors import cors
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Text, String, Integer, Float, DateTime, select, delete
from datetime import datetime
import os
from dotenv import load_dotenv
from groq import AsyncGroq
import asyncio

load_dotenv()

# Quart (async Flask)
app = Quart(__name__)
app = cors(app, allow_origin="*")

# Async Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///diary.db')
# PostgreSQL async: postgresql+asyncpg://user:pass@host/db
if DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Async SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Async Groq Client
groq_client = AsyncGroq(api_key=os.getenv('GROQ_API_KEY'))

# Models
class Base(DeclarativeBase):
    pass

class Entry(Base):
    __tablename__ = 'entry'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    audio_duration: Mapped[float] = mapped_column(Float, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'language': self.language,
            'timestamp': self.timestamp.isoformat(),
            'audio_duration': self.audio_duration
        }

# Initialize database
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.before_serving
async def startup():
    await init_db()

@app.after_serving
async def shutdown():
    await engine.dispose()

# Routes
@app.route('/api/health', methods=['GET'])
async def health_check():
    return jsonify({'status': 'ok', 'message': 'Server is running'})

@app.route('/api/transcribe', methods=['POST'])
async def transcribe_audio():
    """
    Async transcription using Groq Whisper API
    """
    try:
        files = await request.files
        form = await request.form
        
        if 'audio' not in files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = files['audio']
        language = form.get('language', 'ru')
        
        # Map language codes
        lang_map = {
            'ru-RU': 'ru',
            'en-US': 'en',
            'pt-BR': 'pt',
            'es-ES': 'es',
            'pl-PL': 'pl'
        }
        language_code = lang_map.get(language, language.split('-')[0] if '-' in language else language)
        
        # Read audio file
        audio_data = audio_file.read()
        
        # Async transcription with Groq 0.33.0
        transcription = await groq_client.audio.transcriptions.create(
            file=(audio_file.filename, audio_data),
            model="whisper-large-v3",
            language=language_code,
            response_format="json",
            temperature=0.0
        )
        
        return jsonify({
            'text': transcription.text,
            'language': language_code
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/entries', methods=['GET'])
async def get_entries():
    """Get all entries with async database query"""
    try:
        args = request.args
        start_date = args.get('start_date')
        end_date = args.get('end_date')
        
        async with async_session() as session:
            query = select(Entry)
            
            if start_date:
                query = query.where(Entry.timestamp >= datetime.fromisoformat(start_date))
            if end_date:
                query = query.where(Entry.timestamp <= datetime.fromisoformat(end_date))
            
            query = query.order_by(Entry.timestamp.desc())
            result = await session.execute(query)
            entries = result.scalars().all()
            
            return jsonify([entry.to_dict() for entry in entries])
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/entries', methods=['POST'])
async def create_entry():
    """Create a new entry asynchronously"""
    try:
        data = await request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Text is required'}), 400
        
        async with async_session() as session:
            entry = Entry(
                text=data['text'],
                language=data.get('language', 'ru-RU'),
                audio_duration=data.get('audio_duration')
            )
            
            session.add(entry)
            await session.commit()
            await session.refresh(entry)
            
            return jsonify(entry.to_dict()), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/entries/<int:entry_id>', methods=['GET'])
async def get_entry(entry_id):
    """Get a specific entry"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Entry).where(Entry.id == entry_id)
            )
            entry = result.scalar_one_or_none()
            
            if not entry:
                return jsonify({'error': 'Entry not found'}), 404
            
            return jsonify(entry.to_dict())
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/entries/<int:entry_id>', methods=['PUT'])
async def update_entry(entry_id):
    """Update an entry asynchronously"""
    try:
        data = await request.get_json()
        
        async with async_session() as session:
            result = await session.execute(
                select(Entry).where(Entry.id == entry_id)
            )
            entry = result.scalar_one_or_none()
            
            if not entry:
                return jsonify({'error': 'Entry not found'}), 404
            
            if 'text' in data:
                entry.text = data['text']
            if 'language' in data:
                entry.language = data['language']
            
            await session.commit()
            await session.refresh(entry)
            
            return jsonify(entry.to_dict())
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/entries/<int:entry_id>', methods=['DELETE'])
async def delete_entry(entry_id):
    """Delete an entry asynchronously"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Entry).where(Entry.id == entry_id)
            )
            entry = result.scalar_one_or_none()
            
            if not entry:
                return jsonify({'error': 'Entry not found'}), 404
            
            await session.delete(entry)
            await session.commit()
            
            return jsonify({'message': 'Entry deleted successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['GET'])
async def search_entries():
    """Search entries asynchronously"""
    try:
        args = request.args
        query_text = args.get('q', '')
        
        if not query_text:
            return jsonify([])
        
        async with async_session() as session:
            result = await session.execute(
                select(Entry)
                .where(Entry.text.ilike(f'%{query_text}%'))
                .order_by(Entry.timestamp.desc())
            )
            entries = result.scalars().all()
            
            return jsonify([entry.to_dict() for entry in entries])
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)