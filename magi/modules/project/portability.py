import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class PortabilityChecker:
    """
    P21.d: Portabilidad.
    Comprueba que el proyecto se pueda abrir en otra máquina sin dependencias ocultas o 
    rutas absolutas acopladas al host original.
    """
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        
    def check_portability(self) -> dict:
        """
        Produce el reporte portability.json
        """
        report = {
            "compatible": True,
            "missing_tools": [],
            "absolute_paths_found": []
        }
        
        # 1. Comprobar externals.lock (simulado)
        lock_file = self.project_path / ".magi" / "externals.lock"
        if lock_file.exists():
            # Aquí se leerían las dependencias y se verificaría su disponibilidad en el sistema actual
            pass
            
        # 2. Comprobar que el yaml de configuración no tiene rutas absolutas locales
        config_file = self.project_path / ".magi" / "config.yaml"
        if config_file.exists():
            try:
                content = config_file.read_text(encoding='utf-8')
                # Detección simplificada de rutas absolutas de Windows (C:\) o Linux (/home)
                if "C:\\" in content or "D:\\" in content or "/home/" in content:
                    report["absolute_paths_found"].append("config.yaml")
                    report["compatible"] = False
            except Exception as e:
                logger.error(f"Error leyendo config.yaml: {e}")
                
        # Escribir reporte
        out_path = self.project_path / ".magi" / "portability.json"
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
        except IOError:
            logger.error("No se pudo escribir portability.json")
            
        return report
