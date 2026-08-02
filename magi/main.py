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
        
        # Inyección de MAGI 2.0 (Amplificación)
        from magi.core.hive import MagiHive
        from magi.modules.memory.semantic import SemanticRAG
        from magi.modules.memory.compression import HierarchicalMemory
        from magi.modules.route.providers import get_provider
        
        self.hive = MagiHive()
        self.semantic_rag = SemanticRAG()
        provider = get_provider("claude-code-cli")
        self.hierarchical_memory = HierarchicalMemory(provider)
        
        # Inyección de MAGI 3.0 (Enjambre SOTA 2026)
        from magi.core.blackboard import Blackboard
        from magi.modules.logic.verifier import SymbolicVerifier
        from magi.modules.prompts.optimizer import PromptCompiler
        
        self.blackboard = Blackboard()
        self.verifier = SymbolicVerifier()
        self.prompt_compiler = PromptCompiler(provider)
        
        # Inyección de MAGI 4.0 (Singularidad / Evolución)
        from magi.core.evolution import EvolverAgent
        self.evolver = EvolverAgent(provider, self.verifier)
        
        # Inyección de MAGI 5.0 (Bio-Quantum Octopus)
        from magi.core.octopus import CognitiveCore
        from magi.core.quantum_oracle import QuantumOracle
        self.cognitive_core = CognitiveCore()
        self.quantum_oracle = QuantumOracle()
        
        # Inyección de MAGI 6.0 (Cellular HDC)
        from magi.modules.memory.hyperdimensional import HyperdimensionalMemory
        from magi.core.membrane import SkinMembrane
        self.hdc_memory = HyperdimensionalMemory()
        self.cellular_router = SkinMembrane()
        
        # Inyección de MAGI 7.0 (The Predictive Financial Twin)
        from magi.modules.quant.simulator import MarketDigitalTwin
        self.quant_simulator = MarketDigitalTwin(self.hdc_memory)
        
        logger.info("Subsistema MAGI-KEEP (Memoria Inmutable) inicializado y enlazado.")
        logger.info("Subsistema MAGI-ROUTE (Pasarelas) inicializado y enlazado.")
        logger.info(f"Cortacircuitos de Resiliencia configurado con {len(self.cloud_selector.available_models)} modelos cloud.")
        logger.info("MAGI 2.0 Amplificado: [Colmena, RAG Vectorial, gRPC ready, Memoria Jerárquica]")
        logger.info("MAGI 3.0 SOTA 2026: [Blackboard Swarm, Verificador Neuro-Simbólico, DSPy Optimizer]")
        logger.info("MAGI 4.0 Singularidad: [Motor de Evolución Genética y Self-Modifying Code]")
        logger.info("MAGI 5.0 Bio-Quantum: [Octopus Topology y Oráculo QML]")
        logger.info("MAGI 6.0 Cellular HDC: [Memoria Hiperdimensional 10k-bits y Enrutador P-System]")
        logger.info("MAGI 7.0 Predictive Twin: [CFD HFT, Montecarlo y Risk-Off Geopolítico]")
        
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
        if hasattr(self, 'hive') and self.hive:
            self.hive.shutdown()
            
        if hasattr(self, 'kernel') and self.kernel:
            await self.kernel.shutdown()
            logger.info("Sistema apagado correctamente.")
            if hasattr(self, 'cellular_router'):
                self.cellular_router.shutdown()

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
    
    # 3. Lanzar WebView en el Hilo Principal (Bloqueante)
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
