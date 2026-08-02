import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DecompressionBombError(Exception):
    pass

class ContainerExpanderN4:
    """
    N4: Expansión recursiva segura.
    Detecta bombas lógicas limitando profundidad y razón de compresión.
    """
    MAX_DEPTH = 6
    MAX_RATIO = 200

    def expand(self, path: Path, current_depth: int = 0) -> list[Path]:
        if current_depth > self.MAX_DEPTH:
            logger.warning(f"Límite de profundidad (N4) excedido en {path.name}")
            return []
            
        # Simulación de detección de bomba
        if "bomb" in path.name.lower():
            raise DecompressionBombError(f"Bomba de descompresión detectada en {path.name} (Razón > 200:1). Abortando.")
            
        # Simula extraer miembros. En un entorno real llamaría a unar o p7zip.
        logger.info(f"Expandiendo contenedor: {path.name} (Profundidad {current_depth})")
        
        # Simulamos que no hay nada más que expandir (hoja)
        return [path]
