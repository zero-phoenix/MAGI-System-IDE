import os
import sys
import logging
import tempfile

logger = logging.getLogger(__name__)

class SingleInstanceGuard:
    """
    Garantiza que sólo se ejecute una instancia del proceso del núcleo por usuario (A21-1).
    Usa Mutex nombrado en Windows y fcntl.flock en Linux.
    """
    def __init__(self, app_id: str = "MagiSystem"):
        self.app_id = app_id
        self.is_windows = sys.platform == "win32"
        self._lock = None
        self._fd = None

    def acquire(self) -> bool:
        """
        Intenta adquirir el candado de instancia única.
        Retorna True si es la primera instancia, False si ya hay otra corriendo.
        """
        if self.is_windows:
            return self._acquire_windows()
        else:
            return self._acquire_unix()

    def _acquire_windows(self) -> bool:
        try:
            import win32event
            import win32api
            import winerror
            
            mutex_name = f"Global\\{self.app_id}_SingleInstanceMutex"
            self._lock = win32event.CreateMutex(None, 1, mutex_name)
            
            if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
                # Ya existe otra instancia
                self._lock = None
                return False
                
            return True
            
        except ImportError:
            logger.warning("pywin32 no instalado. Guardia de instancia ignorado en modo fallback.")
            return True

    def _acquire_unix(self) -> bool:
        import fcntl
        
        lock_file = os.path.join(tempfile.gettempdir(), f"{self.app_id}.lock")
        try:
            self._fd = os.open(lock_file, os.O_CREAT | os.O_RDWR)
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (IOError, OSError):
            if self._fd:
                os.close(self._fd)
                self._fd = None
            return False

    def release(self):
        """Libera el candado (se llama al cerrar la aplicación)."""
        if self.is_windows and self._lock:
            import win32api
            win32api.CloseHandle(self._lock)
            self._lock = None
        elif not self.is_windows and self._fd:
            import fcntl
            fcntl.flock(self._fd, fcntl.LOCK_UN)
            os.close(self._fd)
            self._fd = None
