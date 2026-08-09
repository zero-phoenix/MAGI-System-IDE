"""
Backend g4f con FAMILIA FIJADA — el arreglo del bug central de v5.0.28.

EL BUG
======
magi/core/providers/cloud.py:117-123 (v5.0.28):

    async def generate(self, system_prompt, user_prompt, model="gpt-4o"):
        if model in ["claude-3.5-sonnet", "qwen-2.5", "deepseek"]:
            model = "gpt-4o"

y luego, en _fetch_from_provider(), la llamada iba SIN parámetro `provider`:

    response = await self.client.chat.completions.create(model=cand, messages=[...])

Resultado: los tres nodos del enjambre pedían familias distintas, las tres se
reescribían a gpt-4o, y g4f auto-ruteaba las tres al mismo sitio. Melchior,
Balthasar y Casper eran EL MISMO MODELO con tres prompts. Por eso las críticas
de Balthasar sonaban genéricas: un modelo criticándose a sí mismo encuentra poco.

EL ARREGLO
==========
g4f sí permite fijar proveedor: create(..., provider=g4f.Provider.Qwen).
Cada instancia de G4FProvider representa UNA familia con una cadena de
candidatos (proveedor, modelo). Si un candidato cae, se prueba el siguiente
DENTRO DE LA MISMA FAMILIA — nunca se salta a otra familia en silencio, porque
eso es justo lo que rompía la diversidad.

Todo gratuito, sin claves de API, sin modelos locales (§I.3 del documento de
arquitectura).
"""
from __future__ import annotations

import asyncio
import logging
import sys
import time
from typing import Any, AsyncIterator, Iterable

from ...no_browser import install as install_browser_guard

from ..base import (
    BaseProvider, CompletionRequest, CompletionResponse, Delta,
    ProviderError, ProviderUnavailable, Usage,
)

logger = logging.getLogger(__name__)

# (nombre de proveedor g4f, modelo o None para el por defecto del proveedor)
Candidate = tuple[str, str | None]

# Catálogo por familia.
#
# VERIFICADO EMPÍRICAMENTE, no leído de los metadatos de g4f. El catálogo
# anterior se construyó filtrando por `working=True and needs_auth=False`, que
# es lo que g4f DICE de sí mismo. Al probar los 44 candidatos uno a uno contra
# la red real (2026-08-06, g4f 7.9.4, cortafuegos §I.3 puesto) respondieron 11:
#
#   HuggingSpace              default              890ms   OK
#   Groq                      default              922ms   OK
#   CohereForAI_C4AI_Command  command-a-03-2025   1078ms   OK
#   CopilotApp                default             1156ms   OK
#   AnyProvider               gpt-4o              1671ms   OK
#   Yqcloud                   gpt-4               2000ms   OK
#   WeWordle                  gpt-4o              2389ms   OK
#   Gemini                    gemini-3.5-flash    3421ms   OK
#   Perplexity                auto                7921ms   OK (respuesta pobre)
#   AnyProvider               default             8014ms   OK
#   Ollama                    default             8139ms   EXCLUIDO: es local (§I.3)
#
# Y fallaron, con su motivo real: PhindAi (timeout), Qwen (error de sesión),
# Claude (pide browser_cookie3), LMArena (pide fichero de auth), OpenaiChat y
# Copilot (piden .har), Pollinations (402), GLM (captcha), MetaAI (403),
# GeminiPro (429), Cloudflare y DeepInfra (INTENTARON ABRIR CHROME, bloqueados).
#
# Las familias que se quedaron sin ningún candidato vivo (deepseek, qwen,
# claude, glm) se conservan a propósito: son el mapa de lo que existe, y
# `complete()` las reporta como agotadas en vez de fingir. El reparto del
# enjambre apunta ahora a las tres familias verificadas.
_FAMILY_SPECS_BASE: dict[str, list[Candidate]] = {
    # --- familias con candidato verificado -------------------------------
    "gpt": [
        ("Yqcloud", "gpt-4"),                    # verificado 2000ms
        ("WeWordle", "gpt-4o"),                  # verificado 2389ms
        ("CopilotApp", None),                    # verificado 1156ms
        ("OpenaiChat", "gpt-5"),                 # pide .har; se deja al final
        ("Pollinations", None),
    ],
    "gemini": [
        ("Gemini", "gemini-3.5-flash"),          # verificado 3421ms
        ("Gemini", "gemini-3.1-pro"),
        ("GeminiPro", None),
    ],
    "command": [
        ("CohereForAI_C4AI_Command", "command-a-03-2025"),   # verificado 1078ms
        ("CohereForAI_C4AI_Command", "command-r-plus"),
    ],
    "llama": [
        ("Groq", None),                          # verificado 922ms
        ("MetaAI", None),
        ("DeepInfra", None),                     # abre navegador: va el último
    ],
    "perplexity": [("Perplexity", "auto")],      # verificado 7921ms
    "hf": [("HuggingSpace", None)],              # verificado 890ms

    # --- familias sin candidato vivo hoy -----------------------------------
    #
    # Se conservan como mapa de lo que existe, pero sus candidatos ROTOS se
    # marcan y NO se intentan (ver `_ROTOS`). Dejarlos vivos costaba caro: el
    # registro del usuario muestra seis intentos fallidos por ronda antes de
    # llegar a un proveedor que pudiera responder, dos de ellos intentando
    # abrir Chrome. `complete()` reporta la familia como agotada, que es lo
    # honesto, pero sin gastar el turno en llamadas imposibles.
    "deepseek": [
        ("PhindAi", "deepseek-v3"),
        ("PhindAi", "deepseek"),
        ("Cloudflare", "deepseek-coder-6.7b"),          # abre navegador
        ("Cloudflare", "deepseek-distill-qwen-32b"),    # abre navegador
    ],
    "qwen": [
        ("Qwen", "qwen3.7-plus"),
        ("Qwen", "qwen3.6-plus"),
        ("Qwen", "qwen3.7-max"),
    ],
    "claude": [
        ("Claude", None),
        ("LMArena", "claude-sonnet-4"),
    ],
    "glm": [("GLM", None)],

    # Último recurso: auto-router de g4f. Familia "auto" para que el registro
    # sepa que NO garantiza diversidad y lo declare en la GUI.
    "auto": [("AnyProvider", "gpt-4o"), ("AnyProvider", "default")],
}

# Familias con al menos un candidato que respondió en la verificación. El
# registro las prefiere al repartir el enjambre.
_VERIFICADAS_BASE = ("gpt", "gemini", "command", "llama", "perplexity", "hf")

#: Proveedores que NO pueden responder en este entorno, con el motivo medido.
#:
#: No es una lista de «va lento» ni de «a veces falla»: es de «no existe forma
#: de que conteste, y comprobarlo cuesta un turno». El registro del usuario
#: mostraba esto en CADA ronda del enjambre:
#:
#:   PhindAi: BaseSession.__init__() got an unexpected keyword argument 'proxy'
#:   Claude:  MissingRequirementsError: Install "browser_cookie3" package
#:   LMArena: No auth file found and nodriver is not available
#:   Cloudflare: BrowserBlocked: MAGI no abre navegadores (§I.3)
#:
#: Seis intentos condenados antes de llegar a uno vivo. Saltárselos no pierde
#: nada —ninguno podía contestar— y `complete()` sigue reportando la familia
#: como agotada, que es la información verdadera.
#:
#: Cada entrada lleva su motivo para que se pueda revisar: si g4f arregla la
#: incompatibilidad de `proxy`, se quita la línea y PhindAi vuelve.
_ROTOS_BASE: dict[str, str] = {
    "PhindAi": "incompatible con la versión instalada de curl_cffi "
               "(BaseSession.__init__() no acepta 'proxy')",
    "Qwen": "AsyncSession.request() no acepta 'proxy' en esta versión",
    "Claude": "exige el paquete browser_cookie3 y cookies de un navegador",
    "LMArena": "exige fichero de autenticación y nodriver",
    "GLM": "responde con captcha",
    "MetaAI": "responde 403 desde esta red",
    "OpenaiChat": "exige un fichero .har de sesión",
    "Copilot": "exige un fichero .har de sesión",
    "Pollinations": "responde 402 (pago requerido)",
    "GeminiPro": "responde 429 (cuota agotada)",
    "Ollama": "es un motor LOCAL: lo prohíbe §I.3",
    # Estos dos no tienen NINGUNA vía que no sea abrir Chrome: su único camino
    # es CDPSession, que el cortafuegos corta siempre. Aquí no es una
    # preferencia, es que no pueden contestar. Distinto de `Gemini`, que
    # declara usar navegador y sin embargo responde por HTTP: ese se queda,
    # solo que el último de su familia.
    "Cloudflare": "su única vía es CDPSession (abrir Chrome), bloqueada por §I.3",
    "DeepInfra": "su única vía es SyncCDPSession (abrir Chrome), bloqueada por §I.3",
}

#: Margen antes de cubrir una petición lenta con el siguiente candidato.
#: 4 s sale de las latencias medidas: los candidatos sanos contestan entre
#: 0,9 y 3,4 s, así que a los 4 s ya no es "va lento", es "algo pasa".
_HEDGE_AFTER_S_BASE = 4.0

#: Tope de llamadas simultáneas por familia. Con 2 se cubre el caso que duele
#: —un candidato colgado— sin convertir cada petición en una tormenta de
#: peticiones contra proveedores gratuitos.
_HEDGE_MAX_BASE = 2

# Reparto por defecto del enjambre.
#
# Antes: MELCHIOR=deepseek, BALTHASAR=claude, CASPER=qwen. Esas tres familias
# NO tienen hoy ni un candidato vivo (deepseek solo respondía vía Cloudflare,
# o sea abriendo una ventana de Chrome; claude pide cookies de navegador; qwen
# devuelve error de sesión). El enjambre quedaba sin proveedor y caía al
# clasificador por defecto, que es justo lo que se ve en el log del usuario.
#
# Ahora apunta a tres familias verificadas y de linajes realmente distintos
# —OpenAI, Google y Cohere—, que es lo que §1.1 pide de verdad: que el crítico
# tenga sesgos distintos al proponente.
_REPARTO_BASE = {
    "MELCHIOR": "gpt",
    "BALTHASAR": "gemini",
    "CASPER": "command",
}


# ---------------------------------------------------------------------------
# Los nombres públicos salen del CATÁLOGO, no de las constantes de arriba.
#
# Las constantes se conservan íntegras como `_*_BASE` y actúan de respaldo: si
# el JSON falta, no valida o trae un esquema desconocido, estos valores salen
# de ellas y todo funciona exactamente igual que antes.
#
# Lo que se gana: arreglar un proveedor caído pasa de recompilar 158 MB de
# ejecutable a editar `%LOCALAPPDATA%\MagiSystem\catalogo_proveedores.json`.
# Ver `core/providers/catalogo.py`.
# ---------------------------------------------------------------------------
from magi.core.providers.catalogo import catalogo as _catalogo   # noqa: E402

_CAT = _catalogo()

FAMILY_SPECS: dict[str, list[Candidate]] = _CAT.family_specs
VERIFIED_FAMILIES: tuple[str, ...] = _CAT.verificadas
ROTOS: dict[str, str] = _CAT.rotos
HEDGE_AFTER_S: float = _CAT.hedge_tras_s
HEDGE_MAX: int = _CAT.hedge_max
DEFAULT_SWARM_FAMILIES: dict[str, str] = _CAT.reparto

#: Tope de caracteres del prompt. ANTES NO HABÍA NINGUNO: se mandaba lo que
#: hiciera falta y, si no cabía, el error se leía como "proveedor roto" y se
#: rotaba a otro que fallaba por lo mismo.
VENTANA_CONTEXTO: int = _CAT.ventana_contexto


def recargar_catalogo() -> dict:
    """
    Relee el catálogo sin reiniciar MAGI. Para el botón de la pestaña
    Configuración: editas el JSON, pulsas, y ya está.
    """
    global _CAT, FAMILY_SPECS, VERIFIED_FAMILIES, ROTOS
    global HEDGE_AFTER_S, HEDGE_MAX, DEFAULT_SWARM_FAMILIES, VENTANA_CONTEXTO
    _CAT = _catalogo(recargar=True)
    FAMILY_SPECS = _CAT.family_specs
    VERIFIED_FAMILIES = _CAT.verificadas
    ROTOS = _CAT.rotos
    HEDGE_AFTER_S = _CAT.hedge_tras_s
    HEDGE_MAX = _CAT.hedge_max
    DEFAULT_SWARM_FAMILIES = _CAT.reparto
    VENTANA_CONTEXTO = _CAT.ventana_contexto
    return _CAT.informe()


def informe_catalogo() -> dict:
    return _CAT.informe()


# Marcadores de código que delatan a un provider capaz de lanzar un navegador.
# Se buscan en el FUENTE del módulo, no en lo que el provider declara de sí
# mismo: Cloudflare y DeepInfra declaran `use_nodriver = False` y aun así abren
# Chrome con CDPSession(headless=False). Fiarse de la declaración fue lo que
# dejó pasar el bug durante tres intentos de arreglo.
_BROWSER_MARKERS = (
    "CDPSession", "SyncCDPSession", "get_shared_browser",
    "get_nodriver", "get_args_from_nodriver", "get_args_from_webview",
    "webview.create_window", "import webbrowser",
)

# Respaldo para el .exe. `inspect.getsource` no funciona dentro de un bundle
# de PyInstaller: el fuente .py no viaja, solo el .pyc. Sin esta lista, el
# binario publicado intentaría Cloudflare antes que a un candidato limpio (el
# cortafuegos lo cortaría igual, así que no hay ventana, pero se gasta un
# intento y el orden deja de coincidir con el de desarrollo). Se mantiene
# corta y explícita: es un respaldo, no la defensa.
_BROWSER_PROVIDERS_CONOCIDOS = frozenset({
    "Cloudflare", "DeepInfra", "Gemini", "OpenaiChat", "Copilot",
    "CopilotSession", "CopilotAccount", "LMArena", "Grok", "Pi",
    "GoogleSearch", "HuggingChat", "HailuoAI", "MicrosoftDesigner",
    "OpenaiAccount", "GLM",
})

_browser_cache: dict[str, bool] = {}


def _uses_browser(cls) -> bool:
    """
    True si este proveedor de g4f puede abrir un navegador real.

    REGLA DEL PROYECTO (§I.3): la inferencia es de nube gratuita y SIN abrir
    nada visible al usuario.

    La detección tiene dos niveles:

    1. Lo que el provider declara (`use_nodriver`, `webdriver`). Pilla a
       Gemini y OpenaiChat.
    2. Lo que el provider HACE, leyendo el fuente de su módulo. Pilla a
       Cloudflare y DeepInfra, que declaran `use_nodriver = False` y aun así
       llaman `CDPSession(headless=False)` -> subprocess.Popen(chrome.exe) sin
       `--headless`, o sea una ventana visible. Ese era el bug real: Cloudflare
       es justo el provider que respondía en todos los logs del usuario.

    Leer el fuente en vez de mantener una lista negra hace que la defensa
    siga valiendo cuando g4f añada providers nuevos.
    """
    if getattr(cls, "use_nodriver", False):
        return True
    if getattr(cls, "webdriver", None):
        return True

    key = f"{getattr(cls, '__module__', '')}.{getattr(cls, '__name__', '')}"
    if key in _browser_cache:
        return _browser_cache[key]

    nombre = getattr(cls, "__name__", "")
    try:
        import inspect
        src = inspect.getsource(sys.modules[cls.__module__])
        verdict = any(m in src for m in _BROWSER_MARKERS)
    except Exception:
        # Congelado en el .exe: no hay fuente. Cae al respaldo estático.
        verdict = nombre in _BROWSER_PROVIDERS_CONOCIDOS
    _browser_cache[key] = verdict
    return verdict


def _resolve(name: str):
    """
    Obtiene la clase de proveedor g4f por nombre, o None si no existe.

    NO descarta a los proveedores capaces de abrir navegador; los DEGRADA al
    final de la cola (ver `_ordered`). El cambio es deliberado:

    quien impide que se abra una ventana es el cortafuegos de
    magi/core/no_browser.py, que corta subprocess.Popen a nivel de proceso. Con
    esa garantía puesta, descartar por precaución solo hacía perder proveedores
    buenos: `Gemini` declara `use_nodriver=True` y sin embargo responde por
    HTTP en 3.4s usando cookies en caché. Descartarlo dejaba la familia gemini
    entera sin candidatos a cambio de nada.

    Con el orden degradado, un proveedor así se intenta el último; si de verdad
    trata de abrir Chrome, el cortafuegos lo corta en 0ms y la familia salta al
    siguiente. Se gana disponibilidad sin ceder ni un pixel de §I.3.
    """
    try:
        import g4f.Provider as P
    except ImportError:
        return None
    return getattr(P, name, None)


def _disable_g4f_browser() -> None:
    """
    Activa el cortafuegos de navegador de MAGI (magi/core/no_browser.py).

    Se conserva el nombre porque es el punto de enganche que ya llamaba el
    backend, pero la lógica vive ahora en un módulo propio, con test y con
    `self_test()` para que Naoko pueda comprobar la invariante §I.3 en vivo.

    Se llama en cada `_get_client()` a propósito: `install()` es idempotente y
    reaplica las capas que dependen de g4f, así que da igual si el módulo se
    importó antes o después de que g4f estuviera cargado.
    """
    install_browser_guard()


class G4FProvider(BaseProvider):
    """Un backend = UNA familia, con cadena de candidatos dentro de ella."""

    supports_tools = False      # g4f no expone tool-calling fiable; MAGI lo
                                # emula con protocolo de texto (ver tools/protocol.py)
    supports_vision = True
    supports_stream = True
    is_local = False

    def __init__(self, family: str = "auto",
                 candidates: Iterable[Candidate] | None = None,
                 provider_id: str | None = None):
        if family not in FAMILY_SPECS and candidates is None:
            raise ValueError(f"familia desconocida: {family}")
        self.family = family
        self.id = provider_id or f"g4f-{family}"
        self.candidates: list[Candidate] = list(candidates or FAMILY_SPECS[family])
        self.default_model = self.candidates[0][1] or "default"
        self._client = None
        self._live: Candidate | None = None   # candidato que funcionó la última vez
        #: Latencia media medida por candidato, en ms. Se llena sola con cada
        #: respuesta y ordena los intentos: el catálogo dice quién PUEDE
        #: contestar, esto dice quién contesta RÁPIDO hoy.
        self._latencia: dict[Candidate, float] = {}

    # ------------------------------------------------------------------ setup

    def _get_client(self):
        if self._client is None:
            _disable_g4f_browser()
            try:
                from g4f.client import AsyncClient
            except ImportError as e:
                raise ProviderUnavailable("g4f no instalado: pip install -U g4f") from e
            self._client = AsyncClient()
        return self._client

    async def available(self) -> bool:
        """Disponible si al menos un candidato de la familia existe en g4f."""
        try:
            self._get_client()
        except ProviderUnavailable:
            return False
        return any(_resolve(name) is not None for name, _ in self.candidates)

    def _ordered(self) -> list[Candidate]:
        """
        Orden de intento: los rápidos primero, capaces-de-navegador al final.

        1. Los que solo hablan HTTP, ORDENADOS POR LATENCIA MEDIDA. Los que
           aún no se han probado van justo detrás del más rápido conocido, para
           que se les dé una oportunidad sin castigar al que ya va bien.
        2. Los que podrían intentar abrir un navegador. El cortafuegos los
           corta en 0 ms si lo intentan, así que estar en la lista no cuesta
           nada; ponerlos al final evita gastar ese intento cuando hay una
           alternativa limpia.

        Antes mandaba la afinidad a secas: el último que funcionó iba primero
        para siempre. En el registro del usuario eso dejaba a `Yqcloud` en
        cabeza de la familia gpt aunque una de sus respuestas tardara 13,9 s
        —el pico que arrastraba la etapa entera— habiendo alternativas de 2 s
        en la misma familia. Con la latencia medida el orden se corrige solo.
        """
        def puede_abrir_navegador(c: Candidate) -> bool:
            cls = _resolve(c[0])
            return cls is not None and _uses_browser(cls)

        conocidas = [v for v in self._latencia.values()]
        sin_medir = min(conocidas) if conocidas else 0.0

        def coste(c: Candidate) -> float:
            return self._latencia.get(c, sin_medir)

        # Los ROTOS no entran: no pueden contestar, y comprobarlo cuesta un
        # turno. Cada ronda del enjambre gastaba seis llamadas condenadas de
        # antemano. Si al descartarlos la familia se queda sin nadie,
        # `complete()` la reporta agotada — que es lo que pasaba, solo que sin
        # esperar a comprobarlo seis veces.
        #
        # Los capaces-de-navegador SÍ entran, pero al final. Excluirlos del
        # todo fue un error que este mismo cambio introdujo y que cazó
        # `test_las_familias_verificadas_si_tienen_candidatos`: `Gemini`
        # declara `use_nodriver=True` y sin embargo responde por HTTP en 3,4 s
        # —está en el registro del usuario contestando una y otra vez—, así que
        # descartarlo dejaba la familia gemini ENTERA sin candidatos. Los que
        # de verdad solo saben abrir Chrome (Cloudflare, DeepInfra) están en
        # ROTOS, que es donde les corresponde.
        vivos = [c for c in self.candidates if c[0] not in ROTOS]
        limpios = sorted((c for c in vivos if not puede_abrir_navegador(c)),
                         key=coste)
        degradados = sorted((c for c in vivos if puede_abrir_navegador(c)),
                            key=coste)
        return limpios + degradados

    def motivos_descartados(self) -> dict[str, str]:
        """
        Por qué cada candidato NO se intenta. Lo enseña Configuración.

        Solo lista lo que de verdad queda fuera de `_ordered()`. La primera
        versión también marcaba «abriría un navegador» a candidatos que sí se
        usan —`Gemini` lo declara y responde por HTTP—, y una pantalla de
        diagnóstico que dice que algo está descartado cuando se está usando es
        peor que no tener pantalla.
        """
        en_cola = {n for n, _ in self._ordered()}
        fuera: dict[str, str] = {}
        for nombre, _ in self.candidates:
            if nombre in en_cola:
                continue
            if nombre in ROTOS:
                fuera[nombre] = ROTOS[nombre]
            elif _resolve(nombre) is None:
                fuera[nombre] = "no existe en esta versión de g4f"
            else:
                fuera[nombre] = "descartado por el cortafuegos §I.3"
        return fuera

    def _anota_latencia(self, cand: Candidate, ms: float) -> None:
        """Media móvil: una respuesta lenta suelta no destierra a un candidato."""
        previa = self._latencia.get(cand)
        self._latencia[cand] = ms if previa is None else previa * 0.7 + ms * 0.3

    # ------------------------------------------------------------- inferencia

    async def _pedir(self, cand: Candidate, messages: list, req: CompletionRequest
                     ) -> tuple[Candidate, str]:
        """Una llamada a un candidato. Devuelve (candidato, texto) o lanza."""
        name, model = cand
        cls = _resolve(name)
        if cls is None:
            raise ProviderError(f"{name}: no existe en g4f")
        t0 = time.monotonic()
        kwargs: dict[str, Any] = {"model": model or "", "messages": messages,
                                  "provider": cls}
        if req.temperature is not None:
            kwargs["temperature"] = req.temperature
        resp = await self._get_client().chat.completions.create(**kwargs)
        content = (resp.choices[0].message.content or "") if resp.choices else ""
        if not content.strip():
            raise ProviderError(f"{name}: respuesta vacía")
        self._anota_latencia(cand, (time.monotonic() - t0) * 1000)
        return cand, content

    async def complete(self, req: CompletionRequest) -> CompletionResponse:
        """
        Pide a la familia, con PETICIÓN CUBIERTA.

        Antes se probaban los candidatos en serie: si el primero tardaba 14 s,
        se esperaban los 14 s. Y así fue en el registro del usuario — una sola
        respuesta de `Yqcloud` a 13.953 ms arrastró la etapa entera de
        Melchior, con alternativas de 2 s esperando su turno en la misma
        familia.

        Ahora, si el primer candidato no ha contestado en `HEDGE_AFTER_S`, se
        lanza el siguiente EN PARALELO sin cancelar al primero, y gana el que
        conteste antes. El caso bueno no cambia (una sola llamada, mismo
        coste); el caso malo deja de pagar la cola de latencia entera. Es la
        misma respuesta, antes: no se recorta nada.

        Si un candidato falla en firme, entra el siguiente de inmediato en vez
        de esperar el margen, que es lo que ya hacía la versión en serie.
        """
        started = time.monotonic()
        self._get_client()
        messages = [m.to_wire() for m in req.messages]
        errors: list[str] = []
        cola = [c for c in self._ordered() if _resolve(c[0]) is not None]
        if not cola:
            raise ProviderError(f"familia '{self.family}': ningún candidato existe")

        pendientes: dict[asyncio.Task, Candidate] = {}
        siguiente = 0
        try:
            while pendientes or siguiente < len(cola):
                if siguiente < len(cola) and len(pendientes) < HEDGE_MAX:
                    cand = cola[siguiente]
                    siguiente += 1
                    pendientes[asyncio.ensure_future(
                        self._pedir(cand, messages, req))] = cand

                if not pendientes:
                    break
                espera = HEDGE_AFTER_S if siguiente < len(cola) else req.timeout_s
                hechas, _ = await asyncio.wait(
                    pendientes, timeout=espera,
                    return_when=asyncio.FIRST_COMPLETED)

                if not hechas:
                    continue          # nadie ha contestado: se cubre con otro

                for t in hechas:
                    cand = pendientes.pop(t)
                    try:
                        ganador, content = t.result()
                    except Exception as e:
                        errors.append(f"{cand[0]}: {type(e).__name__}: {e}")
                        logger.debug("[%s] candidato %s falló: %s",
                                     self.id, cand[0], e)
                        continue

                    self._live = ganador
                    usage = Usage(
                        prompt_tokens=sum(self.estimate_tokens(str(m["content"]))
                                          for m in messages),
                        completion_tokens=self.estimate_tokens(content),
                    )
                    nombre, modelo = ganador
                    logger.info("[%s] respondió %s/%s en %.0fms%s",
                                self.id, nombre, modelo or "default",
                                (time.monotonic() - started) * 1000,
                                f" (cubierto x{len(pendientes) + 1})"
                                if pendientes else "")
                    return self._mk_response(
                        content, f"{nombre}/{modelo or 'default'}", started, usage)
        finally:
            # Las llamadas cubiertas que perdieron la carrera se cancelan: la
            # respuesta ya está, seguir esperándolas solo gastaría cuota.
            for t in pendientes:
                t.cancel()

        raise ProviderError(
            f"familia '{self.family}' agotada ({len(self.candidates)} candidatos): "
            + " | ".join(errors[:4]))

    async def stream(self, req: CompletionRequest) -> AsyncIterator[Delta]:
        client = self._get_client()
        messages = [m.to_wire() for m in req.messages]
        errors: list[str] = []

        for name, model in self._ordered():
            cls = _resolve(name)
            if cls is None:
                continue
            seq, emitted = 0, False
            try:
                stream = client.chat.completions.stream(
                    model=model or "", messages=messages, provider=cls)
                async for chunk in stream:
                    piece = ""
                    if getattr(chunk, "choices", None):
                        delta = getattr(chunk.choices[0], "delta", None)
                        piece = getattr(delta, "content", "") or ""
                    if piece:
                        emitted = True
                        yield Delta(text=piece, seq=seq, provider_id=self.id)
                        seq += 1
                if emitted:
                    self._live = (name, model)
                    yield Delta(text="", seq=seq, done=True, provider_id=self.id)
                    return
                errors.append(f"{name}: stream vacío")
            except Exception as e:
                errors.append(f"{name}: {e}")
                if emitted:
                    # Ya salió texto a pantalla; reintentar duplicaría.
                    yield Delta(text="", seq=seq, done=True, provider_id=self.id)
                    return
                continue

        raise ProviderError(f"streaming agotado en familia '{self.family}': "
                            + " | ".join(errors[:3]))

    async def complete_vision(self, req: CompletionRequest,
                              image_data_url: str) -> CompletionResponse:
        """Multimodal (lo que Naoko usa para leer capturas de pantalla)."""
        started = time.monotonic()
        client = self._get_client()
        base = [m.to_wire() for m in req.messages[:-1]]
        last = req.messages[-1]
        base.append({
            "role": "user",
            "content": [
                {"type": "text", "text": last.content if isinstance(last.content, str)
                 else str(last.content)},
                {"type": "image_url", "image_url": {"url": image_data_url}},
            ],
        })
        for name, model in self._ordered():
            cls = _resolve(name)
            if cls is None:
                continue
            try:
                resp = await client.chat.completions.create(
                    model=model or "", messages=base, provider=cls)
                content = (resp.choices[0].message.content or "") if resp.choices else ""
                if content.strip():
                    return self._mk_response(content, f"{name}(vision)", started)
            except Exception:
                continue
        raise ProviderError(f"visión no disponible en familia '{self.family}'")


def build_swarm_providers(
    families: dict[str, str] | None = None,
) -> dict[str, G4FProvider]:
    """Un proveedor por nodo del enjambre, cada uno en su familia."""
    fam = families or DEFAULT_SWARM_FAMILIES
    return {role: G4FProvider(family=f, provider_id=f"g4f-{f}")
            for role, f in fam.items()}
