import asyncio
import logging
import random
import hashlib
import urllib.request
import time
from typing import Optional, List
from magi.core.store.database import MagiDatabase

try:
    import g4f # type: ignore
    from g4f.client import AsyncClient # type: ignore
    from g4f.Provider import ( # type: ignore
        HuggingChat, DeepSeek, OpenRouterFree, Pollinations, You, Copilot, GlhfChat,
        Airforce, BlackboxPro, PhindAi, Puter, LMArena
    )
except ImportError:
    AsyncClient = None
    g4f = None

logger = logging.getLogger(__name__)

class FreeCloudLLM:
    """
    Red Global de IA basada en Ingeniería Inversa - Hiper-Optimizada.
    Implementa Carreras Asíncronas (Parallel Racing), Rotación de Navegadores, Caché
    y un Recolector Autónomo de Proxys para evadir bloqueos de IP.
    """
    def __init__(self):
        if AsyncClient:
            self.client = AsyncClient()
        else:
            self.client = None
            logger.error("G4F no está instalado. Ejecuta 'pip install -U g4f'")

        self.provider_swarm = [
            Airforce, BlackboxPro, PhindAi, Puter, LMArena,
            OpenRouterFree, Pollinations, GlhfChat, Copilot, HuggingChat, You, DeepSeek
        ]
        
        self._health_registry = {}
        self.db = MagiDatabase("magi_brain.db")
        
        # Caché en memoria para latencia cero
        self._cache = {}
        
        # Rotación de Navegadores (Spoofing)
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
        ]
        
        # Piscina de Proxys eliminada: los proxys gratuitos bloqueaban los requests a LLMs
        self.proxies: List[str] = []

    def _refresh_proxies(self):
        """Deshabilitado. G4F maneja internamente la rotación y bypass."""
        pass

    def _is_alive(self, provider) -> bool:
        health = self._health_registry.get(provider.__name__, {"failures": 0, "cooldown_until": 0})
        return time.time() > health["cooldown_until"]

    def _mark_failure(self, provider):
        name = provider.__name__
        if name not in self._health_registry:
            self._health_registry[name] = {"failures": 0, "cooldown_until": 0}
        self._health_registry[name]["failures"] += 1
        self._health_registry[name]["cooldown_until"] = time.time() + 300
        logger.debug(f"[Salud] Proveedor {name} marcado como MUERTO (TTL: 300s).")
        # Log persistence
        asyncio.create_task(self.db.log_provider_failure(name))

    async def _fetch_from_provider(self, model: str, system_prompt: str, user_prompt: str, attempt: int) -> tuple[str, str]:
        """Intenta obtener una respuesta usando el motor de auto-enrutamiento de G4F."""
        if not self.client:
            raise ValueError("G4F client no inicializado")
            
        logger.debug(f"[Enjambre] G4F Auto-Routing para el modelo {model} (Intento {attempt})...")
        
        start_t = time.time()
        try:
            # Quitamos el parámetro 'provider' para que G4F seleccione automáticamente el mejor
            # proveedor libre (OpenCode style / Auto-fallback).
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            content = response.choices[0].message.content
            latency_ms = (time.time() - start_t) * 1000
            
            if content:
                # G4F puede ocultar qué provider exacto usó si hace auto-fallback, 
                # usaremos 'G4F_Auto_Router' para la telemetría empírica.
                provider_name = "G4F_Auto_Router"
                logger.info(f"[Enjambre] ¡VICTORIA! El auto-router completó la tarea en ({latency_ms:.2f}ms).")
                
                # Calcular telemetría empírica (Inteligencia/Complejidad)
                has_code = "```" in content
                word_count = len(content.split())
                role = "Generación" if "MELCHIOR" in system_prompt else "Análisis" if "BALTHASAR" in system_prompt else "Arbitraje"
                
                asyncio.create_task(self.db.log_provider_success(provider_name, latency_ms, has_code, word_count, role))
                
                return (content, provider_name)
            raise ValueError("Respuesta vacía")
        except Exception as e:
            logger.debug(f"[Enjambre] Auto-router falló en intento {attempt}: {e}")
            raise e

    async def generate(self, system_prompt: str, user_prompt: str, model: str = "gpt-4o") -> tuple[str, str]:
        if not self.client:
            return ("[Error: G4F client no inicializado]", "Unknown")
            
        # Mapeo de Resiliencia: Claude y Qwen fallan nativamente en G4F, 
        # enrutamos todo al cerebro más estable para evitar caídas del Enjambre.
        original_model = model
        if model in ["claude-3.5-sonnet", "qwen-2.5", "deepseek"]:
            model = "gpt-4o"
            
        # 1. Comprobar Caché (Cero Latencia)
        cache_key = hashlib.md5(f"{model}_{system_prompt}_{user_prompt}".encode()).hexdigest()
        if cache_key in self._cache:
            logger.info(f"[LLM Cloud] ACIERTO EN CACHÉ. Retornando respuesta en 0ms.")
            return self._cache[cache_key]
            
        # 2. Retries Secuenciales con Auto-Router
        max_retries = 3
        base_delay = 2.0
        
        for attempt in range(1, max_retries + 1):
            logger.info(f"[LLM Cloud] Iniciando petición a la nube para '{model}' (Intento {attempt}/{max_retries})...")
            
            try:
                result_content, result_provider = await self._fetch_from_provider(model, system_prompt, user_prompt, attempt)
                if result_content:
                    self._cache[cache_key] = (result_content, result_provider)
                    return (result_content, result_provider)
            except Exception as e:
                logger.warning(f"[LLM Cloud] Intento {attempt} fallido por completo. Posible 429 Rate Limit o indisponibilidad del modelo.")
                asyncio.create_task(self.db.log_provider_failure("G4F_Auto_Router"))
                
                if attempt < max_retries:
                    delay = base_delay * (2 ** (attempt-1)) + random.uniform(0, 1)
                    logger.info(f"[LLM Cloud] Aplicando backoff exponencial. Esperando {delay:.2f}s...")
                    await asyncio.sleep(delay)
                
        logger.error("[LLM Cloud] Fallo Crítico en el Enjambre real. Agotados todos los reintentos y proveedores.")
        # Retornamos error real para no continuar el flujo simulado, tal como indicó el usuario.
        return ("[Fallo Crítico: El Enjambre completo ha colapsado. Error 429 Rate Limit Exceeded en proveedores. La tarea se aborta.]", "SYSTEM_ERROR")
