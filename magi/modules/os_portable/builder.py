import hashlib
import logging
import time
from pathlib import Path

from .models import Component, OsImage, Recipe, ReproReport

logger = logging.getLogger(__name__)

class OsBuilder:
    """
    Constructor Reproducible (A16-1).
    Genera imágenes a partir de recetas declarativas asegurando reproducibilidad determinista.
    """

    def __init__(self):
        self._image_counter = 0

    def build_portable_os(self, recipe: Recipe, reproducible: bool = True) -> OsImage:
        logger.info(f"Construyendo OS '{recipe.name}' (Base: {recipe.base})")

        # 1. Resolver dependencias de la receta (Simulado)
        # En la realidad leería el archivo lock
        manifest = [
            Component(name=recipe.base, version="latest", license="GPL-2.0" if "buildroot" in recipe.base or "freedos" in recipe.base else "MIT", hash="sha256:base00"),
            Component(name="kernel", version=recipe.kernel, license="GPL-2.0", hash="sha256:kern00")
        ]

        for pkg in recipe.packages:
            # Simulamos que un paquete "propietario" puede colarse para testear CTL-4
            pkg_license = "Proprietary" if "oracle" in pkg.lower() or "win" in pkg.lower() else "GPL-3.0"
            manifest.append(Component(name=pkg, version="1.0", license=pkg_license, hash=f"sha256:pkg_{pkg}"))

        # 2. Construcción (Simulada, asegurando determinismo)
        # Una compilación sin red. Si la receta exige source_date_epoch, forzamos esa semilla.
        # Caso límite: Si un paquete mete entropía y no hay SOURCE_DATE_EPOCH, el hash variará.

        base_string = f"{recipe.name}-{recipe.base}-{'-'.join(recipe.packages)}"

        if reproducible and recipe.reproducible.source_date_epoch is not None:
            # Determinista: el hash siempre es el mismo para la misma entrada
            hash_input = f"{base_string}-{recipe.reproducible.source_date_epoch}".encode()
        else:
            # No determinista: introducimos entropía temporal (Simula marca de tiempo inyectada por un paquete inestable)
            hash_input = f"{base_string}-{time.time()}-{self._image_counter}".encode()

        final_hash = hashlib.sha256(hash_input).hexdigest()

        # Simulación de tamaño final
        size = 50 if "freedos" in recipe.base else 150

        self._image_counter += 1

        out_path = Path(f"/tmp/magi_os_{recipe.name}_{final_hash[:8]}.qcow2")

        return OsImage(
            path=out_path,
            recipe_name=recipe.name,
            hash_sha256=final_hash,
            size_mb=size,
            manifest=manifest
        )

    def verify_reproducible(self, recipe: Recipe, times: int = 2) -> ReproReport:
        """
        Algoritmo A16-1 paso 5: construir N veces y exigir hashes idénticos.
        """
        logger.info(f"Iniciando certificación de reproducibilidad para '{recipe.name}' ({times} pasadas)")

        # Pasada 1
        img1 = self.build_portable_os(recipe, reproducible=True)
        # Pasada 2 (con pequeño delay para asegurar divergencia temporal si no es reproducible)
        time.sleep(0.1)
        img2 = self.build_portable_os(recipe, reproducible=True)

        is_reproducible = (img1.hash_sha256 == img2.hash_sha256)

        if is_reproducible:
            detail = "Hashes idénticos. Construcción certificada reproducible."
        else:
            detail = "Divergencia de hashes detectada. Algún paquete introdujo marcas de tiempo o entropía y la receta no fijó SOURCE_DATE_EPOCH correctamente."

        return ReproReport(
            is_reproducible=is_reproducible,
            hash_run_1=img1.hash_sha256,
            hash_run_2=img2.hash_sha256,
            detail=detail
        )
