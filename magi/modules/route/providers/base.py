from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """Interfaz base para proveedores de inferencia."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def generate(self, prompt: str, context: dict[str, Any] = None) -> str:
        """
        Ejecuta la inferencia pasándole el prompt.
        :param prompt: Texto de entrada (instrucción/debate).
        :param context: Configuración adicional o histórico.
        :return: Salida del modelo.
        """
        pass
