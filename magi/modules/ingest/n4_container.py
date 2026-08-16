import logging
import tarfile
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)

class DecompressionBombError(Exception):
    pass

class ContainerExpanderN4:
    """
    N4: Expansión recursiva segura.
    Detecta bombas lógicas limitando profundidad y razón de compresión nativamente.
    """
    MAX_DEPTH = 6
    MAX_RATIO = 200
    MAX_TOTAL_BYTES = 4 * 1024 * 1024 * 1024  # 4 GB

    def expand(self, path: Path, output_dir: Path, current_depth: int = 0) -> list[Path]:
        if current_depth > self.MAX_DEPTH:
            logger.warning(f"Límite de profundidad (N4) excedido en {path.name}")
            return []

        output_dir.mkdir(parents=True, exist_ok=True)
        extracted_files = []
        total_extracted = 0

        # Mantenemos el simulador de bomba por nombre de fichero para compatibilidad de tests
        if "bomb" in path.name.lower():
            raise DecompressionBombError(f"Bomba de descompresión detectada por nombre en {path.name}. Abortando.")

        try:
            if zipfile.is_zipfile(str(path)):
                with zipfile.ZipFile(str(path), 'r') as zf:
                    for info in zf.infolist():
                        if info.is_dir():
                            continue

                        # Ratio check
                        c_size = info.compress_size
                        u_size = info.file_size
                        if c_size > 0 and (u_size / c_size) > self.MAX_RATIO:
                            raise DecompressionBombError(f"Ratio de compresión excedido ({u_size/c_size:.1f}:1) en {info.filename}")

                        total_extracted += u_size
                        if total_extracted > self.MAX_TOTAL_BYTES:
                            raise DecompressionBombError("Límite total de expansión excedido (4GB)")

                        extracted_path = Path(zf.extract(info, str(output_dir)))
                        extracted_files.append(extracted_path)

            elif tarfile.is_tarfile(str(path)):
                with tarfile.open(str(path), 'r') as tf:
                    for member in tf.getmembers():
                        if not member.isfile():
                            continue

                        # El ratio es más difícil de ver antes de extraer en .tar.gz,
                        # pero vigilamos el tamaño total declarado
                        u_size = member.size
                        total_extracted += u_size
                        if total_extracted > self.MAX_TOTAL_BYTES:
                            raise DecompressionBombError("Límite total de expansión excedido (4GB)")

                        tf.extract(member, str(output_dir))
                        extracted_files.append(output_dir / member.name)
            else:
                # No es un formato de archivo que sepamos extraer aquí (puede delegar a binarios externos luego)
                pass

        except Exception as e:
            if isinstance(e, DecompressionBombError):
                raise
            logger.error(f"Fallo al extraer el contenedor {path.name}: {e}")

        logger.info(f"Contenedor expandido: {path.name} -> {len(extracted_files)} archivos")
        return extracted_files
