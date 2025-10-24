from pathlib import Path
from typing import Protocol


class SpeechToText(Protocol):
    def transcribe(self, audio_path: Path) -> str:
        """Transcribe audio file to text and return plain text."""
        ...