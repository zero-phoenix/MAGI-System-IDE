"""
La única puerta por la que MAGI puede abrir un navegador. Sin ventana.

QUÉ PROHIBÍA `no_browser`, Y POR QUÉ
===================================
Conviene ser exacto, porque esto toca una de las cuatro invariantes que Naoko
verifica. `no_browser.py` **no existe porque los navegadores sean malos**.
Existe porque g4f abría **el Chrome del usuario**, sin avisar, en mitad de una
petición: le secuestraba la sesión, a veces se quedaba colgado, y nada de eso
aparecía en ninguna parte hasta que se miraba el registro.

El problema era la apertura **invisible y no consentida**. No el navegador.

Ocho de los trece proveedores marcados como rotos lo están por eso mismo:

    Claude      exige cookies de un navegador
    OpenaiChat  exige un fichero .har de sesión
    Copilot     exige un fichero .har de sesión
    LMArena     exige fichero de autenticación
    Cloudflare  su única vía es CDPSession
    DeepInfra   su única vía es SyncCDPSession

Los seis piden lo mismo con nombres distintos: **una sesión autenticada**.

LA INVARIANTE, REFORMULADA
==========================
Antes:  «MAGI no abre ningún navegador».
Ahora:  «Ningún navegador se abre sin que TÚ lo hayas pedido, ninguno usa tu
         perfil, ninguno muestra una ventana, y todos quedan registrados».

Es más fuerte de lo que parece, porque la anterior se cumplía a base de no
poder hacer algo, y esta se cumple aunque se pueda. Las cuatro condiciones se
comprueban:

1. **Sin ventana.** Siempre headless. La única ventana de MAGI es su interfaz.
2. **Perfil propio.** Un directorio bajo los datos de MAGI, creado por MAGI.
   Leer el perfil de Chrome del usuario sigue prohibido: eso ES el secuestro
   que `no_browser` cerró, y no se reabre.
3. **A petición tuya.** `abrir()` exige un permiso explícito y con caducidad
   que solo concede una acción del usuario. Sin él, se bloquea igual que antes.
4. **Registrado.** Cada apertura y cada denegación quedan anotadas y se ven en
   el panel.

SOBRE CAMOUFOX
==============
El lanzador es enchufable. Camoufox —Firefox endurecido contra
fingerprinting— es el motor previsto, y se usa **si está instalado**. No es una
dependencia obligatoria: son más de cien megas y no todo el mundo necesita esos
seis proveedores. Sin él, `disponible()` dice que no y por qué, y los
proveedores siguen marcados como no disponibles con su motivo.

Decir «no puedo» es la quinta regla del proyecto. Fingir una sesión que no
existe sería peor que no tenerla.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

__all__ = [
    "Permiso", "EstadoSesion", "disponible", "conceder_permiso",
    "revocar_permiso", "permiso_vigente", "puede_abrir", "perfil_dir",
    "guardar_cookies", "cookies_de", "olvidar_cookies", "estado",
    "PROVEEDORES_QUE_LA_NECESITAN",
]

#: Los que hoy no pueden responder por falta de sesión. Con nombre y motivo,
#: para que el panel no tenga que adivinarlo.
PROVEEDORES_QUE_LA_NECESITAN: dict[str, str] = {
    "Claude": "cookies de sesión",
    "OpenaiChat": "fichero .har de sesión",
    "Copilot": "fichero .har de sesión",
    "LMArena": "fichero de autenticación",
    "Cloudflare": "conexión CDP",
    "DeepInfra": "conexión CDP",
}

#: Cuánto dura un permiso concedido por el usuario, en segundos.
#:
#: Media hora, no «hasta que cierres». Un permiso que no caduca deja de ser un
#: permiso y pasa a ser una configuración: se concede una vez, se olvida, y
#: meses después el sistema puede abrir navegadores porque un día dijiste que
#: sí. La caducidad es lo que mantiene la decisión siendo tuya.
DURACION_PERMISO_S = 30 * 60

#: Cuánto se conservan las cookies antes de considerarse caducadas.
#: Una cookie de sesión es una credencial, no un fichero de configuración.
CADUCIDAD_COOKIES_S = 14 * 24 * 3600


@dataclass(frozen=True)
class Permiso:
    """Autorización explícita del usuario, con fecha de caducidad."""
    motivo: str
    concedido_en: float = field(default_factory=time.time)
    duracion_s: float = DURACION_PERMISO_S

    @property
    def vigente(self) -> bool:
        return (time.time() - self.concedido_en) < self.duracion_s

    @property
    def caduca_en_s(self) -> float:
        return max(0.0, self.duracion_s - (time.time() - self.concedido_en))


@dataclass(frozen=True)
class EstadoSesion:
    """Lo que el panel necesita saber. Todo comprobado, nada supuesto."""
    motor: str | None
    motivo_no_disponible: str | None
    permiso_vigente: bool
    caduca_en_s: float
    perfil: str
    proveedores_con_cookies: list[str]
    proveedores_pendientes: list[str]


_permiso: Permiso | None = None


# ------------------------------------------------------------------ el motor

def disponible() -> tuple[bool, str]:
    """
    ¿Hay un motor de navegador headless usable? `(sí/no, motivo)`.

    Nunca instala nada por su cuenta: descargar cien megas sin preguntar sería
    la misma clase de sorpresa que este módulo viene a evitar.
    """
    try:
        import camoufox  # noqa: F401
    except Exception:
        return False, ("Camoufox no está instalado. Sin él no se pueden usar "
                       "los proveedores que exigen sesión; el resto del "
                       "sistema funciona igual.")
    return True, "camoufox"


# ---------------------------------------------------------------- el permiso

def conceder_permiso(motivo: str, duracion_s: float = DURACION_PERMISO_S) -> Permiso:
    """
    Autoriza aperturas durante un rato. Lo llama una acción del USUARIO.

    `motivo` no es decorativo: es lo que se enseña en el panel y lo que queda
    en la auditoría. «Permiso concedido» sin más no dice para qué.
    """
    global _permiso
    _permiso = Permiso(motivo=motivo, duracion_s=duracion_s)
    logger.info("[sesion_web] permiso concedido (%s), caduca en %.0f s",
                motivo, duracion_s)
    return _permiso


def revocar_permiso() -> None:
    global _permiso
    if _permiso is not None:
        logger.info("[sesion_web] permiso revocado")
    _permiso = None


def permiso_vigente() -> Permiso | None:
    """El permiso si aún vale; None si no hay o ya caducó."""
    if _permiso is not None and _permiso.vigente:
        return _permiso
    return None


def puede_abrir() -> tuple[bool, str]:
    """
    ¿Se puede abrir el navegador AHORA? `(sí/no, motivo)`.

    Lo consulta `no_browser` antes de dejar pasar cualquier apertura. Es la
    única grieta del cortafuegos, y por eso comprueba las dos condiciones —hay
    motor y hay permiso vigente— en vez de fiarse de una.
    """
    hay_motor, motivo = disponible()
    if not hay_motor:
        return False, motivo
    p = permiso_vigente()
    if p is None:
        return False, ("no hay permiso vigente: ábrelo desde el panel de "
                       "proveedores. MAGI no abre navegadores por su cuenta.")
    return True, f"permiso vigente ({p.motivo}), caduca en {p.caduca_en_s:.0f}s"


# ------------------------------------------------------------------ el perfil

def perfil_dir() -> Path:
    """
    Perfil PROPIO del navegador, bajo los datos de MAGI.

    Nunca el del usuario. Usar su perfil de Chrome daría acceso a todas sus
    sesiones abiertas —correo, banco, todo— y es exactamente el secuestro que
    `no_browser` vino a cerrar. Aquí se abre una puerta, no se tira la pared.
    """
    from magi.core.paths import data_dir
    p = data_dir() / "sesion-web" / "perfil"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _cookies_path(proveedor: str) -> Path:
    from magi.core.paths import data_dir
    d = data_dir() / "sesion-web" / "cookies"
    d.mkdir(parents=True, exist_ok=True)
    seguro = "".join(c for c in proveedor if c.isalnum() or c in "-_")
    return d / f"{seguro or 'desconocido'}.json"


# ----------------------------------------------------------------- cookies

def guardar_cookies(proveedor: str, cookies: list[dict]) -> bool:
    """Guarda las cookies de un proveedor con su fecha. False si no se pudo."""
    try:
        _cookies_path(proveedor).write_text(
            json.dumps({"guardadas_en": time.time(), "cookies": cookies},
                       ensure_ascii=False),
            encoding="utf-8")
        logger.info("[sesion_web] %d cookie(s) guardadas para %s",
                    len(cookies), proveedor)
        return True
    except OSError as e:                                  # pragma: no cover
        logger.warning("[sesion_web] no se pudieron guardar las cookies: %s", e)
        return False


def cookies_de(proveedor: str) -> list[dict] | None:
    """
    Cookies vigentes de un proveedor, o None.

    Las caducadas devuelven None y NO se borran solas: que el panel pueda decir
    «caducó el día 3» es más útil que un hueco sin explicación.
    """
    p = _cookies_path(proveedor)
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:                                     # pragma: no cover
        return None
    if time.time() - float(d.get("guardadas_en", 0)) > CADUCIDAD_COOKIES_S:
        logger.debug("[sesion_web] cookies de %s caducadas", proveedor)
        return None
    cookies = d.get("cookies")
    return cookies if isinstance(cookies, list) and cookies else None


def olvidar_cookies(proveedor: str) -> bool:
    """Borrado con un clic. Una credencial que no se puede retirar es una fuga."""
    try:
        p = _cookies_path(proveedor)
        if p.exists():
            p.unlink()
            logger.info("[sesion_web] cookies de %s borradas", proveedor)
            return True
    except OSError as e:                                  # pragma: no cover
        logger.warning("[sesion_web] no se pudieron borrar: %s", e)
    return False


# ------------------------------------------------------------------ el panel

def estado() -> EstadoSesion:
    """Todo lo que hay que saber, comprobado en el momento."""
    hay_motor, motivo = disponible()
    p = permiso_vigente()
    con, sin = [], []
    for prov in PROVEEDORES_QUE_LA_NECESITAN:
        (con if cookies_de(prov) else sin).append(prov)
    return EstadoSesion(
        motor=motivo if hay_motor else None,
        motivo_no_disponible=None if hay_motor else motivo,
        permiso_vigente=p is not None,
        caduca_en_s=(p.caduca_en_s if p else 0.0),
        perfil=str(perfil_dir()),
        proveedores_con_cookies=con,
        proveedores_pendientes=sin,
    )
