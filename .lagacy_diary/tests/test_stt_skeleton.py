from pathlib import Path

from services.stt import SpeechToText, DummySTT, get_stt


def test_dummy_stt_transcribe(tmp_path: Path):
    audio = tmp_path / "test_audio.ogg"
    audio.write_bytes(b"OggS\x00dummy")

    stt: SpeechToText = DummySTT()
    out = stt.transcribe(audio)
    assert "dummy transcript" in out
    assert "test_audio.ogg" in out


def test_get_stt_factory_dummy():
    stt = get_stt("dummy")
    assert isinstance(stt, DummySTT)