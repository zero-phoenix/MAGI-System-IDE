"""
Contrato único de proveedores de inferencia (Plan MAGI 9.0 §1.1).

El problema que resuelve: en v5.0.28, `FreeCloudLLM.generate()` reescribía
'deepseek', 'claude-3.5-sonnet' y 'qwen-2.5' a 'gpt-4o' antes de salir
(cloud.py:122-123), de modo que los tres agentes del enjambre eran el mismo
modelo con tres prompts. La regla de diversidad del documento de arquitectura
(§I.3.2) no se cumplía.

Aquí un proveedor declara su FAMILIA, y el registro garantiza que Melchior,
Balthasar y Casper obtengan familias distintas cuando sea posible — y lo
declare abiertamente cuando no lo sea.
"""
from __future__ import annotations

import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal, Protocol, runtime_checkable

Role = Literal["system", "user", "assistant", "tool"]


class ProviderState(str, Enum):
    CLOSED = "closed"        # sano
    OPEN = "open"            # cortacircuitos disparado
    HALF_OPEN = "half_open"  # sonda de recuperación


@dataclass
class Message:
    role: Role
    content: str | list[dict[str, Any]]
    tool_call_id: str | None = None
    name: str | None = None

    def to_wire(self) -> dict[str, Any]:
        d: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        if self.name:
            d["name"] = self.name
        return d


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class CompletionRequest:
    messages: list[Message]
    model: str | None = None
    temperature: float = 0.4
    max_tokens: int | None = None
    tools: list[dict[str, Any]] | None = None
    timeout_s: float = 120.0
    seed: int | None = None
    stream: bool = False
    #: Es una SONDA (canario de deriva, medición de latencia): su respuesta
    #: es corta POR DISEÑO y su fallo es un dato, no una penalización. El
    #: tráfico de sonda no se juzga con las reglas del tráfico real ni
    #: castiga al cortacircuitos — si no, medir la salud enferma al sistema.
    probe: bool = False
    #: Política de cobertura (hedge) para ESTA petición:
    #:   True  -> lanzar candidatos de cubierta en paralelo (HEDGE_MAX)
    #:   False -> una sola llamada, sin cubierta. Quien llama ya tiene
    #:            redundancia estructural (variantes o ejes en paralelo).
    #:   None  -> auto: el backend decide por la latencia medida de la familia.
    #:
    #: EL MULTIPLICADOR QUE EL LOG DEL 16-AGO DEMOSTRÓ. Cada llamada lógica
    #: con hedge x3 disparaba 2-3 llamadas HTTP reales; en una sola petición
    #: eso multiplicó ~16 llamadas lógicas hasta ~50 HTTP. La redundancia
    #: estructural (N variantes de Melchior, N ejes de Balthasar) ya cubre el
    #: caso "candidato lento": forzar hedge AHÍ es pagarlo dos veces.
    hedge: bool | None = None
    #: Etiqueta para la traza: `tarea/ronda/paso/rama`. Sin esto, el log de
    #: backends no permite saber de qué petición salió cada llamada — el log
    #: del 16-ago era ininteligible: 50 líneas sin tarea ni ronda.
    tag: str = ""
    #: TECHO DE RELOJ PARA LA CADENA ENTERA (v5.8.0 §E1), no para un intento.
    #:
    #: `timeout_s` acota UN candidato. El failover prueba hasta `max_attempts`
    #: (3), y cada uno estrenaba su propio techo: 3 × 150 s = 450 s de pared
    #: para una sola llamada lógica, sin que nadie lo acotara ni lo dijera.
    #:
    #: No es teórico. `token_ledger` de este equipo, 2026-08-20:
    #:
    #:     CASPER   / gemini   n=10   mediana  44 726 ms   máx  390 391 ms
    #:     MELCHIOR / gemini   n=35   mediana  25 000 ms   máx  355 078 ms
    #:     MELCHIOR / gpt      n=33   mediana  50 906 ms   máx  138 641 ms
    #:
    #: 390 segundos —seis minutos y medio— en una sola llamada. El usuario ve
    #: la ventana quieta y concluye, con razón, que el sistema no responde.
    #:
    #: El presupuesto se reparte: cada intento recibe lo que QUEDA, nunca más.
    #: Con el valor por defecto igual a `timeout_s`, ningún candidato pierde
    #: tiempo respecto a hoy — lo que desaparece es la multiplicación.
    presupuesto_s: float | None = None


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class CompletionResponse:
    content: str
    provider_id: str
    family: str
    model: str
    usage: Usage = field(default_factory=Usage)
    tool_calls: list[ToolCall] = field(default_factory=list)
    latency_ms: float = 0.0
    degraded: str | None = None   # motivo si la diversidad se rompió

    @property
    def wants_tools(self) -> bool:
        return bool(self.tool_calls)


@dataclass
class Delta:
    """Fragmento de una respuesta en streaming."""
    text: str = ""
    seq: int = 0
    done: bool = False
    provider_id: str = ""


class ProviderError(RuntimeError):
    """Fallo recuperable: el registro probará con otro proveedor."""


class ProviderTimeout(ProviderError):
    """La llamada excedió timeout_s. En v5.0.28 esto no existía y una
    petición colgada congelaba el enjambre indefinidamente."""


class ProviderUnavailable(ProviderError):
    """El proveedor no está instalado / autenticado / accesible."""


@runtime_checkable
class Provider(Protocol):
    id: str
    family: str            # "claude" | "qwen" | "deepseek" | "gemini" | "gpt" | ...
    supports_tools: bool
    supports_vision: bool
    supports_stream: bool
    is_local: bool

    async def available(self) -> bool: ...
    async def complete(self, req: CompletionRequest) -> CompletionResponse: ...
    def stream(self, req: CompletionRequest) -> AsyncIterator[Delta]: ...


class BaseProvider:
    """Base con utilidades comunes. Los backends heredan de aquí."""

    id: str = "base"
    family: str = "unknown"
    supports_tools: bool = False
    supports_vision: bool = False
    supports_stream: bool = False

    def mejor_latencia_ms(self) -> float | None:
        """La respuesta más rápida medida de este proveedor, o None.

        Un backend sin mediciones devuelve None: «no lo sé» no debe
        confundirse con «es rápido». La usa el registry para el techo de
        espera dinámico (v6.0 §A7).
        """
        return None
    is_local: bool = False
    default_model: str = ""

    async def available(self) -> bool:
        return True

    async def complete(self, req: CompletionRequest) -> CompletionResponse:
        raise NotImplementedError

    async def stream(self, req: CompletionRequest) -> AsyncIterator[Delta]:
        """Fallback: si el backend no soporta streaming real, emite la
        respuesta completa como un único delta. Así la GUI puede tratar a
        todos los proveedores igual."""
        resp = await self.complete(req)
        yield Delta(text=resp.content, seq=0, done=True, provider_id=self.id)

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Aproximación barata (~4 chars/token). Suficiente para presupuestar;
        los backends que devuelven usage real lo sobrescriben."""
        return max(1, len(text) // 4)

    def _mk_response(
        self, content: str, model: str, started: float,
        usage: Usage | None = None, tool_calls: list[ToolCall] | None = None,
    ) -> CompletionResponse:
        return CompletionResponse(
            content=content,
            provider_id=self.id,
            family=self.family,
            model=model,
            usage=usage or Usage(),
            tool_calls=tool_calls or [],
            latency_ms=(time.monotonic() - started) * 1000.0,
        )


# ---------------------------------------------------------------------------
# C11 — UN FALLO QUE VIENE COMO TEXTO SIGUE SIENDO UN FALLO
# ---------------------------------------------------------------------------
#
# El sistema tiene dos formas de devolver un error DISFRAZADO de respuesta
# normal, y las dos son cadenas de texto corrientes:
#
#   · `cloud.py` -> "[Inferencia no disponible: ...]" con provider_id
#     "SYSTEM_ERROR".
#   · `agent_loop.py` -> "[Tiempo de espera agotado tras 150s...]" con
#     `AgentTurn.degraded` puesto.
#
# Quien no mire el proveedor se las traga como contenido bueno. Eso es
# EXACTAMENTE lo que produjo, en las tres pruebas del 2026-08-20, un
# «**Decisión Técnica:** APPROVED» seguido del mensaje de error: el árbitro no
# recibió nada, el texto no tenía marcador de decisión y el respaldo aprobaba
# por defecto. También fue lo que dejó a Ritsuko firmando un veredicto que era
# el error del proveedor.
#
# Por eso la comprobación vive AQUÍ, en un solo sitio, y no repartida en cada
# consumidor: una regla que hay que acordarse de aplicar en cinco ficheros es
# una regla que se aplica en cuatro.

#: Proveedores sintéticos que en realidad significan «no hubo respuesta».
PROVEEDORES_DE_FALLO = ("SYSTEM_ERROR", "TIMEOUT")

#: Cómo empieza el texto de una respuesta degradada.
MARCAS_DEGRADADAS = (
    "[Inferencia no disponible",
    "[Tiempo de espera agotado",
    "[RITSUKO] No he podido emitir veredicto",
    "todos los proveedores fallaron",
)


def es_degradada(texto: str | None, provider_id: str | None = None) -> bool:
    """
    ¿Esto es un fallo con forma de respuesta?

    Se mira primero el `provider_id`, que es la señal de máquina y no depende
    de cómo esté redactado el mensaje; el texto es la red por si la respuesta
    viene de un camino que aún no marca el proveedor.
    """
    if provider_id and provider_id in PROVEEDORES_DE_FALLO:
        return True
    t = (texto or "").strip()
    if not t:
        return True
    cabeza = t[:240]
    return any(m in cabeza for m in MARCAS_DEGRADADAS)
