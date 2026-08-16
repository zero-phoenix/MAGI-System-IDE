import logging
from pathlib import Path

from .secrets import SecretScanner

logger = logging.getLogger(__name__)

# Intenta importar pygit2 de forma segura
try:
    import pygit2
    HAS_PYGIT2 = True
except ImportError:
    HAS_PYGIT2 = False
    logger.warning("pygit2 no instalado. Operaciones Git desactivadas.")

class ProjectRepository:
    """
    Gestión del repositorio Git local (P21.c).
    Nunca realiza push automático. Protegido por CTL-9 y CTL-1.
    """
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.scanner = SecretScanner()

    def init_repo(self) -> bool:
        if not HAS_PYGIT2:
            return False

        try:
            # Inicializa repo desnudo o estándar
            repo_path = self.project_path
            if not (repo_path / ".git").exists():
                pygit2.init_repository(str(repo_path), bare=False)
                logger.info(f"Repositorio Git inicializado en {repo_path}")
            return True
        except Exception as e:
            logger.error(f"Error inicializando repo Git: {e}")
            return False

    def check_pre_sync(self, files_to_commit: list[str]) -> tuple[bool, list]:
        """A21-3: Comprueba CTL-9 (secretos) y CTL-1 (archivos excluidos) antes de sync."""
        issues = []
        for file in files_to_commit:
            filepath = self.project_path / file
            if not filepath.exists() or filepath.is_dir():
                continue

            # CTL-9: Barrido de secretos
            findings = self.scanner.scan_file(str(filepath))
            if findings:
                issues.append(f"[CTL-9 Bloqueo] Secreto en {file}: {findings[0]}")

            # CTL-1: Regla de volcado de hardware
            # (Simplificado: si el archivo es un binario .bin o .rom en un directorio específico)
            if file.endswith('.bin') or file.endswith('.rom'):
                issues.append(f"[CTL-1 Bloqueo] Archivo de firmware/volcado excluido: {file}")

        return len(issues) == 0, issues

    def status(self) -> dict:
        if not HAS_PYGIT2:
            return {"error": "pygit2 no disponible"}

        repo = pygit2.Repository(str(self.project_path))
        status_dict = repo.status()
        return {filepath: flags for filepath, flags in status_dict.items()}
