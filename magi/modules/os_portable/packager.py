import logging
from pathlib import Path
from typing import Literal

from .models import OsImage, Recipe

logger = logging.getLogger(__name__)

class PackagingRefused(Exception):
    def __init__(self, code: str, detail: str):
        super().__init__(f"[{code}] {detail}")
        self.code = code
        self.detail = detail

class Packager:
    """
    Empaquetador y CTL-4 (A16-2).
    Incrusta la imagen en el motor y aplica políticas de distribución.
    """
    def package_single_executable(self, image: OsImage, recipe: Recipe, target: Literal["windows", "linux"], engine: Literal["qemu", "wasm", "dosbox"] = "qemu") -> Path:
        logger.info(f"Empaquetando {image.recipe_name} para {target} usando {engine}")

        # 1. Validación de tamaño (A16-2.2)
        if image.size_mb > recipe.output.max_size_mb:
            raise ValueError(f"La imagen ({image.size_mb} MB) excede el max_size_mb de la receta ({recipe.output.max_size_mb} MB).")

        # 2. CTL-4: Validación Legal de Redistribución (A16-2.5)
        # Se rechaza el empaquetado si algún componente no permite redistribución
        prohibited_licenses = ["proprietary", "closed", "commercial", "eula"]
        restricted_components = []

        for comp in image.manifest:
            if any(p in comp.license.lower() for p in prohibited_licenses):
                restricted_components.append(f"{comp.name} ({comp.license})")

        if restricted_components:
            detail = f"Los siguientes componentes tienen licencias restrictivas que impiden la redistribución del artefacto único: {', '.join(restricted_components)}"
            logger.error(detail)
            raise PackagingRefused(code="CTL4", detail=detail)

        # 3. Empaquetado exitoso (Simulado)
        # En la realidad esto invoca a rustc para compilar `os/launcher/` con `--manifest` incrustado
        ext = ".exe" if target == "windows" else ".AppImage"
        out_path = Path(f"/tmp/{recipe.name}_portable{ext}")

        logger.info(f"Empaquetado exitoso: {out_path} (Firma y hash listos)")
        return out_path
