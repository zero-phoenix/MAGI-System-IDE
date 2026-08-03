import asyncio
import logging
import argparse
import sys
import os
import signal
import threading
import webview
from magi.gui_server import GUIServer

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from magi.core.kernel import Kernel
from magi.modules.resilience.selector import CloudSelector
from magi.modules.route.gateway import Gateway
from magi.modules.memory.composer import Composer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("MagiSystem")

class MagiSystem:
    """
    Orquestador principal del MAGI System IDE (Área 0 y Centro de Control).
    Amarra el bus de eventos, la pasarela de UI, la resiliencia cloud y los módulos operativos.
    """
    def __init__(self, host="127.0.0.1", port=20128, debug=False):
        self.host = host
        self.port = port
        self.debug = debug
        if self.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            
        self.kernel = Kernel(host=self.host, port=self.port)
        self.bus = self.kernel.bus
        # Inicialización de Resiliencia Cloud-Only (Área 6)
        self.cloud_selector = CloudSelector(["cloud-openai-gpt4", "cloud-anthropic-claude", "cloud-google-gemini", "cloud-mistral", "cloud-cohere"])
        self._shutdown_event = asyncio.Event()

    async def _setup_signal_handlers(self):
        """Maneja el apagado limpio (Graceful Shutdown)"""
        if sys.platform != 'win32':
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, self._shutdown_event.set)
        else:
            # En Windows no podemos usar add_signal_handler directamente de la misma forma,
            # pero asyncio.run se encarga de KeyboardInterrupt.
            pass

    async def start(self):
        logger.info("Iniciando MAGI System IDE...")
        
        # 1. Setup de señales
        await self._setup_signal_handlers()
        
        # 2. Levantar el Kernel (Área 0)
        await self.kernel.start()
        
        # 3. Levantar otros módulos base
        self.gateway = Gateway()
        from magi.modules.memory.record import MemoryRecord
        self.record = MemoryRecord("main_session")
        self.composer = Composer(self.record)
        
        # ---------------------------------------------------------------
        # MAGI 9.0 — Regla "conecta o borra".
        #
        # v5.0.28 instanciaba aquí doce subsistemas (MagiHive, SemanticRAG,
        # HierarchicalMemory, SymbolicVerifier, PromptCompiler, EvolverAgent,
        # CognitiveCore, QuantumOracle, HyperdimensionalMemory, SkinMembrane,
        # MarketDigitalTwin...). Conteo real de sitios de llamada:
        #
        #     self.semantic_rag.*        -> 0     self.cognitive_core.*  -> 0
        #     self.hierarchical_memory.* -> 0     self.quantum_oracle.*  -> 0
        #     self.prompt_compiler.*     -> 0     self.hdc_memory.*      -> 0
        #     self.evolver.*             -> 0     self.quant_simulator.* -> 0
        #     self.hive.*                -> 1  (solo .shutdown())
        #     self.cellular_router.*     -> 1  (solo .shutdown())
        #
        # Los dos únicos que se usaban, se usaban para APAGARLOS. Existían para
        # que se imprimieran las líneas "MAGI 5.0 Bio-Quantum", "MAGI 7.0
        # Predictive Twin", etc.
        #
        # Se retiran. Lo que queda está conectado y tiene tests.
        # ---------------------------------------------------------------
        from magi.core.providers.cloud import get_registry
        from magi.core.context import refresh_context

        self.provider_registry = await get_registry()
        self.exec_context = refresh_context(
            provider_health=self.provider_registry.telemetry())

        assignment = self.provider_registry.select_for_swarm()
        logger.info("Enjambre: %s", " · ".join(
            f"{r}={assignment.families.get(r, 'n/d')}" for r in assignment.by_role))
        if assignment.diversity != "full":
            logger.warning("Diversidad %s: %s", assignment.diversity, assignment.note)

        fams = self.provider_registry.families_available()
        logger.info("Inferencia: %d familias de nube gratuita sanas -> %s",
                    len(fams), ", ".join(fams) or "NINGUNA")
        logger.info("Datos en: %s", __import__("magi.core.paths", fromlist=["x"]).data_dir())

        logger.info("SISTEMA MAGI OPERATIVO Y ESPERANDO CONEXIONES.")
        
        # 4. Mantener vivo hasta apagado
        try:
            if sys.platform == 'win32':
                # Bucle de espera compatible con Windows
                while not self._shutdown_event.is_set():
                    await asyncio.sleep(1)
            else:
                await self._shutdown_event.wait()
        except KeyboardInterrupt:
            logger.info("Interrupción por teclado detectada.")
            
        await self.stop()

    async def stop(self):
        logger.info("Deteniendo el sistema MAGI...")
        if hasattr(self, 'kernel') and self.kernel:
            await self.kernel.shutdown()
            logger.info("Sistema apagado correctamente.")

def _start_magi_background(magi, loop):
    """Ejecuta el loop asyncio en un hilo secundario"""
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(magi.start())
    except Exception as e:
        logger.error(f"Error fatal en el loop secundario: {e}")

def main():
    parser = argparse.ArgumentParser(description="MAGI System IDE Bootstrapper")
    parser.add_argument("--host", default="127.0.0.1", help="Host para el GUI Server (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=20128, help="Puerto para el GUI Server (default: 20128)")
    parser.add_argument("--gui-port", type=int, default=1420, help="Puerto HTTP local para el Frontend (default: 1420)")
    parser.add_argument("--debug", action="store_true", help="Habilitar logs de depuración")
    
    args = parser.parse_args()
    
    magi = MagiSystem(host=args.host, port=args.port, debug=args.debug)
    
    # 1. Iniciar Servidor GUI Estático
    gui = GUIServer(port=args.gui_port)
    gui.start()
    
    # 2. Iniciar el Kernel MAGI en un Hilo Secundario
    magi_loop = asyncio.new_event_loop()
    magi_thread = threading.Thread(target=_start_magi_background, args=(magi, magi_loop), daemon=True)
    magi_thread.start()
    
    import sys
    import os
    
    def get_resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    logger.info("Iniciando ventana nativa de MAGI...")
    webview.create_window(
        title="MAGI System IDE",
        url=f"http://127.0.0.1:{args.gui_port}",
        width=1280,
        height=800,
        frameless=False,
        easy_drag=False
    )
    
    # Esto bloqueará hasta que el usuario cierre la ventana
    webview.start(debug=args.debug)
    
    # 4. Apagado Limpio al cerrar la ventana
    logger.info("Ventana cerrada. Apagando sistemas...")
    gui.stop()
    
    # Señalizar al loop que se detenga
    if sys.platform != 'win32':
        magi_loop.call_soon_threadsafe(magi._shutdown_event.set)
    else:
        # Hack simple para despertar y apagar en Windows
        magi_loop.call_soon_threadsafe(magi._shutdown_event.set)
        
    magi_thread.join(timeout=3)
    logger.info("MAGI cerrado por completo. Adiós.")
    sys.exit(0)

if __name__ == "__main__":
    main()
