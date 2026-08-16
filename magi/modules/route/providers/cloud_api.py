import asyncio
import logging
from typing import Any

from .base import BaseProvider

logger = logging.getLogger(__name__)

class CloudAPIProvider(BaseProvider):
    """
    Wrapper genérico para llamadas HTTP REST a APIs de nube (Gemini, OpenAI, etc).
    """
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def generate(self, prompt: str, context: dict[str, Any] | None = None) -> str:
        logger.info(f"[{self._name}] Enviando solicitud HTTP REST al cloud...")
        await asyncio.sleep(0.3)
        return f"[{self._name} API Responde] Analizado: {prompt[:30]}..."
