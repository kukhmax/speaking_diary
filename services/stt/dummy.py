from pathlib import Path

from .base import SpeechToText


class DummySTT:
    """A trivial STT that returns a synthetic text based on filename."""

    def transcribe(self, audio_path: Path) -> str:
        name = audio_path.name
        return f"[dummy transcript for {name}]"


def get_stt(provider: str = "dummy") -> SpeechToText:
    if provider == "dummy":
        return DummySTT()
    raise ValueError(f"Unsupported STT provider: {provider}")