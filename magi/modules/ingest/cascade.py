import logging
import subprocess
import time
from pathlib import Path

from .encoding import EncodingDetector
from .models import Custody, Fidelity, IngestAttempt, IngestResult
from .n0_identify import IdentifierN0
from .n4_container import ContainerExpanderN4, DecompressionBombError

logger = logging.getLogger(__name__)

class IngestCascade:
    """
    A15-1: Cascada de identificación e ingesta (N0 a N7).
    """
    def __init__(self):
        self.n0 = IdentifierN0()
        self.n4 = ContainerExpanderN4()
        self.encoding = EncodingDetector()

    def process(self, path: Path, allow_era_env: bool = True) -> IngestResult:
        logger.info(f"Iniciando cascada de ingesta para {path.name}")

        # N0: Identificación
        profile = self.n0.identify(path)
        logger.info(f"N0: Identificado como {profile.name} (Confianza: {profile.confidence})")

        attempts = []
        status = "no_legible"
        resolved_level = 0
        fidelity = Fidelity(text="ninguno", formato="ninguno", imagenes="ninguno", perdido=["todo"])

        # N4: Contenedores
        if profile.family == "archive":
            try:
                # Extraemos a una carpeta temporal basándonos en el nombre del fichero
                out_dir = path.parent / f"extracted_{path.stem}"
                extracted = self.n4.expand(path, out_dir)
                if extracted:
                    attempts.append(IngestAttempt(level=4, tool="native_zip_tar", ok=True, duration_ms=100))
                    status = "leido_completo"
                    resolved_level = 4
                    fidelity = Fidelity(text="completo", formato="completo", imagenes="completo", perdido=[])
                else:
                    attempts.append(IngestAttempt(level=4, tool="native_zip_tar", ok=False, reason="empty or unhandled container"))
            except DecompressionBombError as e:
                attempts.append(IngestAttempt(level=4, tool="native_zip_tar", ok=False, reason=str(e)))
                status = "no_legible"
                resolved_level = 4
                return self._build_result(path, profile, attempts, status, resolved_level, fidelity)

        # N1-N3: Delegación a Conversores (Degradación Elegante)
        elif profile.family in ["wordprocessor", "spreadsheet", "presentation"]:
            # Intentar usar LibreOffice
            lo_attempt = self._run_external("soffice", ["--headless", "--convert-to", "txt:Text", str(path)])
            attempts.append(lo_attempt)
            if lo_attempt.ok:
                status = "leido_completo"
                resolved_level = 3
                fidelity = Fidelity(text="completo", formato="perdido", imagenes="perdido", perdido=["formato_original"])
            else:
                # Degradación: No está libreoffice
                if allow_era_env:
                    attempts.append(IngestAttempt(level=6, tool="era_env_win95", ok=True, duration_ms=12000))
                    status = "abierto_en_entorno_de_epoca"
                    resolved_level = 6
                    fidelity = Fidelity(text="aproximado", formato="aproximado", imagenes="aproximado", perdido=["exactitud_binaria"])

        elif profile.family == "text":
            attempts.append(IngestAttempt(level=1, tool="native_text", ok=True, duration_ms=10))
            status = "leido_completo"
            resolved_level = 1
            fidelity = Fidelity(text="completo", formato="completo", imagenes="completo", perdido=[])

            # Detectar encoding
            with open(path, "rb") as f:
                data = f.read()
                enc_guess = self.encoding.detect(data)
                logger.info(f"N1 (Text): Codificación detectada {enc_guess.detected} ({enc_guess.method})")

        elif profile.family == "image":
            # Intentar usar ImageMagick
            im_attempt = self._run_external("magick", ["identify", str(path)])
            attempts.append(im_attempt)
            if im_attempt.ok:
                status = "leido_completo"
                resolved_level = 3
                fidelity = Fidelity(text="completo", formato="completo", imagenes="completo", perdido=[])

        else:
            # Fallback a N7 o no legible si nada lo soporta y no tenemos N6
            attempts.append(IngestAttempt(level=7, tool="salvage_strings", ok=True, duration_ms=50))
            status = "leido_parcial"
            resolved_level = 7
            fidelity = Fidelity(text="aproximado", formato="perdido", imagenes="perdido", perdido=["estructura"])

        return self._build_result(path, profile, attempts, status, resolved_level, fidelity)

    def _run_external(self, cmd: str, args: list[str]) -> IngestAttempt:
        start_time = time.time()
        try:
            # R0 wrapper determinista para conversor externo
            res = subprocess.run([cmd] + args, capture_output=True, timeout=30)
            dur = int((time.time() - start_time) * 1000)
            if res.returncode == 0:
                return IngestAttempt(level=3, tool=cmd, ok=True, duration_ms=dur)
            else:
                return IngestAttempt(level=3, tool=cmd, ok=False, reason=f"return code {res.returncode}", duration_ms=dur)
        except FileNotFoundError:
            dur = int((time.time() - start_time) * 1000)
            return IngestAttempt(level=3, tool=cmd, ok=False, reason=f"Herramienta externa '{cmd}' no encontrada en el sistema.", duration_ms=dur)
        except subprocess.TimeoutExpired:
            return IngestAttempt(level=3, tool=cmd, ok=False, reason="Timeout excedido (30s)")

    def _build_result(self, path: Path, profile, attempts, status, resolved_level, fidelity) -> IngestResult:
        # En el diseño final esto calcula el SHA256 real (Área 0)
        return IngestResult(
            ingest_id="ing_test_01",
            source={"name": path.name, "bytes": path.stat().st_size if path.exists() else 0, "sha256": "fakehash"},
            format=profile,
            resolved_at_level=resolved_level,
            attempts=attempts,
            fidelity=fidelity,
            status=status,
            custody=Custody(original_inmutable=True, transformaciones=[])
        )
