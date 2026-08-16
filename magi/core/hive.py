import asyncio
import concurrent.futures
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

class MagiHive:
    """
    Pilar 1: Computación Distribuida (La Colmena).
    Permite delegar tareas pesadas (CPU bound o dependientes de I/O bloqueante)
    fuera del hilo principal asíncrono, simulando un esquema de Celery/Redis workers.
    """
    def __init__(self, max_workers: int = 4):
        self.executor = concurrent.futures.ProcessPoolExecutor(max_workers=max_workers)

    async def delegate_task(self, task_name: str, func: Callable, *args) -> Any:
        """
        Ejecuta la función en un proceso secundario y devuelve el resultado de forma asíncrona.
        """
        logger.debug(f"[HIVE] Delegando tarea pesada '{task_name}' a worker distribuido...")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(self.executor, func, *args)
        logger.debug(f"[HIVE] Tarea '{task_name}' completada.")
        return result

    def shutdown(self):
        self.executor.shutdown(wait=True)
