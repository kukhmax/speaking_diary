from typing import Protocol, Optional


class LLM(Protocol):
    def generate(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate a response given a prompt and optional context."""
        ...