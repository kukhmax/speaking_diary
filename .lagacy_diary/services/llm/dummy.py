from typing import Optional

from .base import LLM


class DummyLLM:
    """A trivial LLM that echoes the prompt and optional context."""

    def generate(self, prompt: str, context: Optional[str] = None) -> str:
        base = f"[dummy reply] {prompt}"
        if context:
            base += f" | ctx={context}"
        return base


def get_llm(provider: str = "dummy") -> LLM:
    if provider == "dummy":
        return DummyLLM()
    raise ValueError(f"Unsupported LLM provider: {provider}")