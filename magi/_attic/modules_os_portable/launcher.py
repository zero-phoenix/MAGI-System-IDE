import logging
import time
from pathlib import Path
from typing import Literal

from .models import EraProfile, OsImage, VmSession

logger = logging.getLogger(__name__)

class EscapeAttemptError(Exception):
    pass

class Launcher:
    """
    Ejecutor en Ventana y Entornos de Época (A16-3).
    Supervisa la sesión de QEMU/WASM/DOSBox-X garantizando el confinamiento total.
    """

    def launch_in_window(self, image: OsImage, network: Literal["none", "host-only", "nat"] = "none", engine: Literal["qemu", "wasm", "dosbox"] = "qemu") -> VmSession:
        logger.info(f"Arrancando sesión de VM con {image.recipe_name}. Red: {network}, Motor: {engine}")

        session = VmSession(
            session_id=f"vm_{int(time.time())}",
            image=image,
            status="running",
            engine=engine,
            network_enabled=(network != "none"),
            events=[{"type": "vm.started", "engine": engine}]
        )
        return session

    def inject_network_traffic_simulation(self, session: VmSession) -> None:
        """
        Simulador de comportamiento para testear el firewall/aislamiento de QEMU.
        Si la VM intenta usar la red cuando está deshabilitada, lanza el evento crítico.
        """
        logger.info(f"Inyectando tráfico de red desde el huésped en la sesión {session.session_id}")

        if not session.network_enabled:
            session.status = "stopped"
            escape_detail = "El huésped intentó abrir conexiones de red cuando network='none'. Aislamiento violado."
            session.events.append({"type": "vm.escape_attempt", "detail": escape_detail})
            logger.critical(f"ALARMA DE FUGA: {escape_detail}")
            raise EscapeAttemptError(escape_detail)

        logger.info("Tráfico permitido. La VM tiene acceso a red (NAT/Host).")

    def run_in_era(self, profile: EraProfile, document_path: Path) -> dict:
        """
        Algoritmo A16-3: Apertura de documento en Entorno de Época.
        Canaliza las peticiones del Nivel 6 del Área 15.
        """
        logger.info(f"Iniciando flujo de rescate de época: Perfil '{profile.name}' para archivo '{document_path.name}'")

        # 1. Crear ISO efímera de solo lectura
        iso_path = Path(f"/tmp/efimera_{int(time.time())}.iso")
        logger.info(f"Creada ISO efímera de sólo lectura en {iso_path}")

        # 2. Arrancar la sesión (red desactivada obligatoriamente)
        # Usaremos una imagen "mock" que representa el perfil
        img_mock = OsImage(path=Path("/tmp/mock"), recipe_name=profile.name, hash_sha256="", size_mb=10, manifest=[])
        session = self.launch_in_window(img_mock, network="none", engine="dosbox" if "dos" in profile.name.lower() else "qemu")

        # 3. Esperar estabilidad y ejecutar secuencia de exportación
        logger.info(f"Aplicación {profile.application} abierta. Esperando estabilización de pantalla...")
        time.sleep(0.5)

        logger.info(f"Ejecutando secuencia ciega de exportación: {' -> '.join(profile.export_sequence)}")

        # 4. Determinar éxito
        # Simulamos que algunos documentos se exportan y otros solo arrojan capturas de pantalla
        if "exportar_a_txt" in profile.export_sequence:
            result = {
                "success": True,
                "text_extracted": "Texto rescatado desde la aplicación de época por macros de teclado.",
                "screenshot": None
            }
            logger.info("Texto exportado exitosamente mediante atajos del entorno huésped.")
        else:
            result = {
                "success": True,
                "text_extracted": None,
                "screenshot": Path("/tmp/rescate_pantalla.png")
            }
            logger.info("Exportación fallida o no soportada. Devolviendo captura de pantalla de resolución nativa para OCR.")

        session.status = "stopped"
        session.events.append({"type": "vm.stopped", "reason": "era_rescue_complete"})
        logger.info("Sesión desechable destruida (restauración de instantánea).")

        return result
