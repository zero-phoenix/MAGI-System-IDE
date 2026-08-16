import logging

from magi.core.bus import MagiBus
from magi.core.store.database import MagiDatabase

logger = logging.getLogger(__name__)

class BusLogger:
    """
    Observador Omnisciente.
    Se suscribe al MagiBus y graba todas las acciones de los Agentes
    en la Base de Datos SQLite, sin interferir con la lógica del Enjambre.
    """
    def __init__(self, bus: MagiBus, db: MagiDatabase):
        self.bus = bus
        self.db = db

        # Suscribir a los tópicos de interés
        self.bus.subscribe("SYS_EXEC", self._handle_sys_exec)
        self.bus.subscribe("AGENT_POST", self._handle_agent_post)

        logger.info("[Logger] Observer conectado al MagiBus. Memoria Inmutable activada.")

    async def _handle_sys_exec(self, event):
        """Intercepta cuando el usuario lanza una orden."""
        payload = event.payload
        task_id = payload.get("task_id", "UNKNOWN")
        command = payload.get("command", "")

        await self.db.save_task(task_id, command)

    async def _handle_agent_post(self, event):
        """Intercepta las contribuciones de los agentes al debate."""
        payload = event.payload
        # El task_id normalmente viene en el contexto general, pero el payload del AGENT_POST actual
        # en agents.py no manda task_id ni round_num explícitamente en el payload emitido a la UI.
        # Vamos a intentar extraerlo si existe, o usar un default.
        # En una mejora futura, podemos inyectar task_id en el BusEvent de los agentes.
        task_id = payload.get("task_id", "ACTIVE_TASK")
        round_num = payload.get("round_num", 1)
        agent_name = payload.get("agent", "UNKNOWN")
        role = payload.get("role", "UNKNOWN")
        provider = payload.get("provider", "UNKNOWN")
        content = payload.get("content", "")

        await self.db.save_debate_entry(task_id, round_num, agent_name, role, provider, content)
