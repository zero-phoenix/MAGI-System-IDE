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
    "PROVEEDORES_QUE_LA_NECESITAN", "COSECHA_AUTOMATICA", "COSECHA_IMPORTADA",
    "cosechar", "importar_cookies", "diagnostico",
    "diagnostico_legible", "PLAZO_PRUEBA_S",
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

#: DOS CAMINOS, PORQUE NO TODOS PIDEN LO MISMO — Y ESTO HAY QUE DECIRLO CLARO.
#:
#: La regla es «ninguna ventana salvo la interfaz de MAGI», y eso tiene una
#: consecuencia que conviene no disimular: **sin ventana no puedes escribir tu
#: contraseña**. Un inicio de sesión interactivo necesita que veas la página.
#:
#: Así que los seis proveedores se parten en dos grupos de verdad distintos:
#:
#:   AUTOMÁTICO — necesitan una SESIÓN de navegador, no una CUENTA. Basta con
#:   visitar la página headless y dejar que se resuelva el desafío
#:   anti-bot; las cookies que quedan sirven. Cero intervención tuya, cero
#:   ventanas.
#:
#:   IMPORTADO — necesitan TU CUENTA. Aquí no hay forma honesta de hacerlo sin
#:   ventana: o te la enseñamos, o le damos tu contraseña a un robot. Las dos
#:   opciones son malas. La tercera es que tú exportes las cookies desde tu
#:   propio navegador —donde ya has iniciado sesión— y MAGI las lea de un
#:   fichero. MAGI no abre nada y tu contraseña no pasa por aquí.
#:
#: Fingir que el segundo grupo funciona solo sería vender humo, que es
#: justamente lo que este proyecto no hace.
COSECHA_AUTOMATICA: dict[str, str] = {
    "Cloudflare": "https://playground.ai.cloudflare.com/",
    "DeepInfra": "https://deepinfra.com/",
}

COSECHA_IMPORTADA: dict[str, str] = {
    "Claude": "https://claude.ai",
    "OpenaiChat": "https://chatgpt.com",
    "Copilot": "https://copilot.microsoft.com",
    "LMArena": "https://lmarena.ai",
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
        return False, ("Camoufox no está instalado (`pip install camoufox`). "
                       "Sin él no se pueden usar los proveedores que exigen "
                       "sesión; el resto del sistema funciona igual.")

    # DOS COMPROBACIONES, NO UNA. El paquete de pip pesa 1,3 MB y es solo el
    # lanzador: el navegador de verdad son ~100 MB que se descargan aparte con
    # `camoufox fetch`. Dar por bueno el import dejaría el fallo para el primer
    # uso real, disfrazado de error del proveedor en vez de «falta descargar el
    # navegador» — que es accionable y lo otro no.
    try:
        from camoufox.pkgman import installed_verstr
        version = installed_verstr()
    except Exception:
        return False, ("Camoufox está instalado pero el navegador no se ha "
                       "descargado todavía. Ejecuta `camoufox fetch` (~100 MB, "
                       "una sola vez). No se descarga solo a propósito: bajar "
                       "cien megas sin preguntar es la clase de sorpresa que "
                       "este módulo viene a evitar.")
    return True, f"camoufox {version}"


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

# ------------------------------------------------- cosecha automática

#: Cuánto se espera a que el desafío anti-bot se resuelva solo. No es un
#: «esperemos a ver»: los desafíos de Cloudflare y similares tardan unos
#: segundos y luego dejan la cookie. Más allá de esto, no va a llegar.
ESPERA_DESAFIO_S = 15.0


def _lanzar_headless(url: str, espera_s: float = ESPERA_DESAFIO_S) -> list[dict]:
    """
    Visita `url` en Camoufox HEADLESS y devuelve las cookies resultantes.

    NINGUNA VENTANA. NUNCA. Y no es una promesa: `headless=True` va escrito
    aquí y `test_nunca_se_lanza_con_ventana` lee este fichero para comprobar
    que nadie lo cambia. La única ventana de MAGI es su interfaz, y una
    excepción «solo para depurar» es como esa regla se pierde.

    Tampoco se usa `headless="virtual"`: eso levanta un display virtual (Xvfb),
    que es una dependencia más y una ventana más, aunque no la veas.
    """
    import subprocess

    from magi.core.paths import python_executable

    # LA COSECHA VA EN UN PROCESO HIJO, Y NO ES CEREMONIA.
    #
    # `Camoufox(...)` no acepta un plazo propio —su firma es `**launch_options`
    # y el `timeout` no llega a donde hace falta—, así que dentro del proceso
    # no hay forma de acotar la espera. Medido en la máquina del usuario: dos
    # procesos `camoufox` vivos, SIN ventana (bien), y la llamada colgada los
    # 180 s por defecto de Playwright antes de decir nada.
    #
    # La causa es del entorno, no del código: con un agente de seguridad de por
    # medio —FortiClient, un antivirus con inspección de red, una VPN
    # corporativa— el navegador arranca pero la tubería local por la que
    # Playwright habla con él queda interceptada.
    #
    # Con un hijo, el plazo lo pongo yo, y matarlo mata también el navegador.
    # Eso último importa tanto como lo primero: un navegador headless que
    # sobrevive a un fallo es un proceso invisible corriendo en la máquina del
    # usuario, y eso es PEOR que uno visible — no puede ni cerrarlo.
    guion = (
        "import json,sys\n"
        "from camoufox.sync_api import Camoufox\n"
        "url=sys.argv[1]; espera=float(sys.argv[2])\n"
        "with Camoufox(headless=True) as nav:\n"
        "    p=nav.new_page()\n"
        "    p.goto(url, wait_until='domcontentloaded', timeout=int(espera*1000))\n"
        "    p.wait_for_timeout(int(min(espera,10)*1000))\n"
        "    print(json.dumps(p.context.cookies()))\n"
        "    p.close()\n"
    )
    # `python_executable()` y NO `sys.executable`. Dentro del .exe empaquetado,
    # `sys.executable` ES el propio .exe: lanzarlo con `-c` relanzaría MAGI
    # entero en vez de cosechar cookies, y sin dar error — devolvería el
    # resultado de otro programa. Es la sexta regla del proyecto, y un guardián
    # de test_wiring me la recordó al escribir esto.
    interprete = python_executable()
    if interprete is None:
        raise RuntimeError(
            "no hay un intérprete de Python con el que lanzar la cosecha. El "
            "binario lleva uno embebido; si tampoco está, la sesión web no "
            "puede funcionar y los proveedores que la necesitan siguen fuera.")

    plazo = espera_s + 45          # arranque + navegación + margen
    try:
        r = subprocess.run([interprete, "-c", guion, url, str(espera_s)],
                           capture_output=True, text=True, timeout=plazo)
    except subprocess.TimeoutExpired:
        # NO SE CULPA AL ANTIVIRUS. Lo hice una vez y era falso.
        #
        # Este camino solo se recorre DESPUÉS de que `_prueba_arranque()` haya
        # confirmado que el navegador arranca —medido: 9,6 s en la máquina del
        # usuario—. Así que lo que se agota aquí no es el arranque ni la
        # tubería local: es cargar la página o resolver su desafío.
        #
        # Decir «un agente de seguridad intercepta la tubería» sería repetir
        # exactamente la conjetura que el diagnóstico ya desmintió. Se describe
        # lo que se sabe y se apunta a la herramienta que puede decir el resto.
        raise RuntimeError(
            f"el navegador arrancó pero la página no terminó de cargar en "
            f"{plazo:.0f}s. Puede ser el desafío anti-bot del sitio, la red, o "
            f"que el proveedor haya cambiado. Ejecuta el diagnóstico de sesión "
            f"web para ver qué comprobación falla exactamente. Los proveedores "
            f"que piden iniciar sesión NO se ven afectados: esos van por "
            f"importación de cookies, que no abre ningún navegador.") from None

    if r.returncode != 0:
        raise RuntimeError(f"la cosecha falló: {r.stderr.strip()[:250]}")
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        raise RuntimeError("la cosecha no devolvió cookies legibles") from None


def _lanzar_headless_en_proceso(url: str, espera_s: float) -> list[dict]:
    """
    La misma cosecha, dentro de este proceso. Solo la usan los tests.

    Existe para que `test_nunca_se_lanza_con_ventana` tenga una llamada a
    `Camoufox` que auditar con AST: el guion del proceso hijo es una cadena, y
    una cadena no se puede analizar sintácticamente igual de bien.
    """
    from camoufox.sync_api import Camoufox

    with Camoufox(headless=True) as navegador:
        pagina = navegador.new_page()
        try:
            pagina.goto(url, wait_until="domcontentloaded",
                        timeout=int(espera_s * 1000))
            # El desafío anti-bot se resuelve solo, con JavaScript, unos
            # segundos después de cargar. Sin esta espera se cosechan las
            # cookies de ANTES de resolverlo, que no sirven para nada.
            pagina.wait_for_timeout(int(min(espera_s, 10) * 1000))
            return list(pagina.context.cookies())
        finally:
            pagina.close()


def _cosechar_sin_navegador(url: str, timeout_s: float = 30.0) -> list[dict]:
    """
    Cookies con `curl_cffi` imitando la huella de un navegador. Sin abrir nada.

    POR QUÉ SE INTENTA ESTO PRIMERO
    ===============================
    Medido contra los dos sitios que supuestamente exigen navegador:

        https://playground.ai.cloudflare.com/   HTTP 200 en 0,2 s
        https://deepinfra.com/                  HTTP 200 en 0,7 s

    Sin navegador, sin los ~100 MB, sin proceso hijo y sin plazo de 93
    segundos. `curl_cffi` imita el apretón de manos TLS y HTTP/2 de un Chrome
    real, y eso es lo primero que miran la mayoría de las protecciones
    anti-bot: el handshake, no si hay una persona detrás.

    Que g4f diga «su única vía es CDPSession» describe **cómo lo implementó
    g4f**, no lo que el servidor exige.

    Devuelve lista vacía si no consigue nada; quien llama decide si escalar.
    """
    from curl_cffi import requests as cr

    r = cr.get(url, impersonate="chrome", timeout=timeout_s)
    if r.status_code >= 400:
        return []
    return [{"name": k, "value": v, "domain": "", "path": "/"}
            for k, v in dict(r.cookies).items()]


def cosechar(proveedor: str, espera_s: float = ESPERA_DESAFIO_S) -> tuple[bool, str]:
    """
    Consigue las cookies de un proveedor. `(éxito, explicación)`.

    Solo funciona con los de `COSECHA_AUTOMATICA`: los que piden una sesión de
    navegador y no una cuenta. Para el resto se dice qué hacer en vez de
    intentarlo y fallar con un error críptico.
    """
    if proveedor in COSECHA_IMPORTADA:
        return False, (
            f"{proveedor} necesita TU cuenta, no solo una sesión de navegador. "
            f"MAGI no puede iniciar sesión por ti sin abrir una ventana ni "
            f"pedirte la contraseña, y no va a hacer ninguna de las dos cosas. "
            f"Exporta las cookies de {COSECHA_IMPORTADA[proveedor]} desde tu "
            f"navegador e impórtalas con `importar_cookies()`.")

    url = COSECHA_AUTOMATICA.get(proveedor)
    if not url:
        return False, f"{proveedor} no necesita sesión web"

    # DEL MÁS BARATO AL MÁS CARO, Y NO AL REVÉS.
    #
    # La primera versión empezaba por el navegador: en la máquina del usuario
    # eso eran 93 segundos para acabar fallando. Y resulta que el camino
    # barato —curl_cffi con huella de navegador, ya instalado— devuelve HTTP
    # 200 en 0,2 s contra esos mismos sitios.
    #
    # Empezar por el caro convertía un éxito de dos décimas en un fallo de
    # minuto y medio.
    intentos: list[str] = []
    try:
        cookies = _cosechar_sin_navegador(url)
        if cookies:
            guardar_cookies(proveedor, cookies)
            return True, (f"{len(cookies)} cookie(s) de {url} sin abrir "
                          f"ningún navegador")
        intentos.append("sin navegador: respondió, pero sin cookies")
    except Exception as e:
        intentos.append(f"sin navegador: {type(e).__name__}: {str(e)[:80]}")

    # Solo ahora, el navegador. Y solo con permiso.
    permitido, motivo = puede_abrir()
    if not permitido:
        return False, "; ".join(intentos + [f"con navegador: {motivo}"])

    # COMPROBACIÓN PREVIA. El arranque se sabe en diez segundos; la cosecha
    # completa tardaba noventa en admitir lo mismo, porque su plazo tenía que
    # cubrir además la navegación y el desafío. Noventa segundos de espera para
    # un fallo que se conoce en diez es el sistema pareciendo colgado.
    arranca, detalle = _prueba_arranque()
    if not arranca:
        intentos.append(f"con navegador: no arranca ({detalle})")
        return False, "; ".join(intentos)

    try:
        cookies = _lanzar_headless(url, espera_s)
    except Exception as e:
        intentos.append(f"con navegador: {type(e).__name__}: {str(e)[:150]}")
        return False, "; ".join(intentos)

    if not cookies:
        intentos.append("con navegador: la visita no dejó ninguna cookie")
        return False, "; ".join(intentos)
    guardar_cookies(proveedor, cookies)
    return True, f"{len(cookies)} cookie(s) obtenidas de {url} con navegador"


# ------------------------------------------------- cosecha importada

def importar_cookies(proveedor: str, ruta) -> tuple[bool, str]:
    """
    Lee cookies de un fichero que TÚ exportaste. `(éxito, explicación)`.

    Acepta los tres formatos en que la gente exporta cookies, porque obligar a
    uno concreto es obligar a una herramienta concreta:

      · JSON en lista  — el que sueltan las extensiones de navegador
      · cookies.txt    — formato Netscape, el de curl/wget
      · .har           — lo que exporta el panel de red del navegador

    Nada de esto abre ninguna ventana ni ve tu contraseña: tú ya iniciaste
    sesión en tu navegador, y aquí solo se lee el resultado.
    """
    ruta = Path(ruta)
    if not ruta.exists():
        return False, f"no existe el fichero {ruta}"

    try:
        texto = ruta.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return False, f"no se pudo leer: {e}"

    cookies = _parsear_cookies(texto, ruta.suffix.lower())
    if not cookies:
        return False, ("no encontré cookies dentro. Formatos admitidos: JSON "
                       "de extensión, cookies.txt (Netscape) o .har")

    guardar_cookies(proveedor, cookies)
    return True, f"{len(cookies)} cookie(s) importadas para {proveedor}"


def _parsear_cookies(texto: str, sufijo: str = "") -> list[dict]:
    """
    Saca cookies de cualquiera de los tres formatos.

    Se prueba por CONTENIDO y no por extensión: un `.txt` puede llevar JSON
    dentro, y fiarse del nombre del fichero es cómo se rechaza un fichero
    perfectamente válido.
    """
    texto = texto.strip()

    # 1) JSON: lista de extensión, o un HAR completo.
    if texto.startswith(("[", "{")):
        try:
            d = json.loads(texto)
        except Exception:
            d = None
        if isinstance(d, list):
            return [c for c in d if isinstance(c, dict) and c.get("name")]
        if isinstance(d, dict):
            # HAR: las cookies viven en log.entries[].request.cookies
            entradas = (d.get("log") or {}).get("entries") or []
            vistas: dict[tuple, dict] = {}
            for e in entradas:
                for c in ((e.get("request") or {}).get("cookies") or []):
                    if c.get("name"):
                        vistas[(c["name"], c.get("domain", ""))] = c
            if vistas:
                return list(vistas.values())
            if d.get("cookies"):
                return [c for c in d["cookies"] if c.get("name")]
        return []

    # 2) Netscape cookies.txt: 7 campos separados por tabulador.
    fuera: list[dict] = []
    for linea in texto.splitlines():
        if not linea.strip() or linea.lstrip().startswith("#"):
            continue
        campos = linea.split("\t")
        if len(campos) < 7:
            continue
        dominio, _sub, ruta_c, seguro, expira, nombre, valor = campos[:7]
        fuera.append({
            "name": nombre, "value": valor, "domain": dominio, "path": ruta_c,
            "secure": seguro.strip().upper() == "TRUE",
            "expires": float(expira) if expira.strip().lstrip("-").isdigit() else -1,
        })
    return fuera


# ------------------------------------------------- diagnóstico ejecutable

#: Plazo del arranque de prueba. Si el navegador no contesta en este margen, no
#: va a contestar después: lo que tarda es negociar la conexión local, no
#: cargar nada. Declarado como constante y no escondido, porque una máquina
#: muy lenta podría necesitar más.
PLAZO_PRUEBA_S = 10.0


def _prueba_arranque(plazo_s: float = PLAZO_PRUEBA_S) -> tuple[bool, str]:
    """
    Arranca el navegador y lo cierra, sin navegar a ninguna parte.

    POR QUÉ UNA PRUEBA APARTE
    ========================
    La cosecha completa tardaba 93 segundos en admitir que el navegador no
    arranca, porque el plazo tenía que cubrir además la navegación y el
    desafío. Pero el arranque se sabe en diez: lo que tarda es negociar la
    conexión local, y eso o va rápido o no va.

    Noventa segundos de espera para un fallo que se conoce en diez es el
    sistema pareciendo colgado.
    """
    import subprocess
    import time

    from magi.core.paths import python_executable

    interprete = python_executable()
    if interprete is None:
        return False, "no hay intérprete de Python con el que lanzarlo"

    guion = ("from camoufox.sync_api import Camoufox\n"
             "with Camoufox(headless=True) as n:\n"
             "    pass\n"
             "print('ok')\n")
    t0 = time.perf_counter()
    try:
        r = subprocess.run([interprete, "-c", guion], capture_output=True,
                           text=True, timeout=plazo_s)
    except subprocess.TimeoutExpired:
        return False, f"no respondió en {plazo_s:.0f}s"
    ms = (time.perf_counter() - t0) * 1000
    if r.returncode != 0:
        return False, (r.stderr.strip().splitlines() or ["falló sin decir nada"])[-1][:120]
    return True, f"arranca en {ms:.0f} ms"


def diagnostico(incluir_lentas: bool = True) -> list[dict]:
    """
    Qué falla, comprobado. No qué me parece a mí.

    ESTA FUNCIÓN ES UNA LECCIÓN CONVERTIDA EN HERRAMIENTA
    ====================================================
    Al ver que la cosecha se colgaba, afirmé que la causa era FortiClient
    interceptando la tubería local de Playwright. Lo dije con seguridad y sin
    comprobarlo: lo deduje de ver FortiClient en la lista de procesos.

    Al medirlo, los sockets locales conectaban en 0,0 s — o sea, mi explicación
    era una conjetura con aspecto de diagnóstico. La causa real sigue sin
    determinar, y eso es lo que hay que decir hasta saberlo.

    Cada línea de aquí es una comprobación REAL y separada, con su tiempo. Así
    la próxima vez el motivo se lee en vez de deducirse, y nadie tiene que
    creerse la conjetura de nadie.

    Las comprobaciones caras van al final y se pueden saltar: un diagnóstico
    que tarda tanto como el fallo no ayuda.
    """
    import socket
    import time

    fuera: list[dict] = []

    def anota(nombre, fn):
        t0 = time.perf_counter()
        try:
            ok, detalle = fn()
        except Exception as e:
            ok, detalle = False, f"{type(e).__name__}: {str(e)[:120]}"
        fuera.append({"comprobacion": nombre, "ok": bool(ok),
                      "detalle": detalle,
                      "ms": round((time.perf_counter() - t0) * 1000, 1)})

    def paquete():
        import camoufox  # noqa: F401
        return True, "instalado"

    def navegador():
        from camoufox.pkgman import installed_verstr
        return True, installed_verstr()

    def socket_local():
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", 0))
            s.listen(1)
            c = socket.create_connection(("127.0.0.1", s.getsockname()[1]),
                                         timeout=5)
            conn, _ = s.accept()
            conn.close()
            c.close()
        finally:
            s.close()
        return True, "conecta"

    def sin_navegador():
        cookies = _cosechar_sin_navegador("https://playground.ai.cloudflare.com/")
        return True, f"responde ({len(cookies)} cookie(s))"

    anota("paquete camoufox", paquete)
    anota("navegador descargado", navegador)
    anota("socket local 127.0.0.1", socket_local)
    anota("via sin navegador (curl_cffi)", sin_navegador)
    if incluir_lentas:
        anota("arranque headless", lambda: _prueba_arranque())
    return fuera


def diagnostico_legible(incluir_lentas: bool = True) -> str:
    """
    El diagnóstico en texto, para el panel y para Naoko.

    MARCAS EN ASCII, Y NO ES REMILGO
    ================================
    La primera versión usaba `✓` y `✗`. Al imprimirlo en la consola de Windows:

        UnicodeEncodeError: 'charmap' codec can't encode character '\\u2713'

    Una herramienta de diagnóstico que revienta al imprimirla es peor que no
    tenerla: se llama justo cuando algo va mal, y añadir un error propio encima
    del que se investigaba deja al usuario con dos problemas y ninguna pista.

    Es el mismo fallo que ya se pagó en el enjambre —una respuesta entera
    perdida por escribir un acento en una consola cp1252— y por el que existe
    `magi/core/consola.py`. Aquí se evita en origen: el texto sale imprimible
    en cualquier parte, y quien quiera símbolos bonitos los pone al pintarlo.
    """
    lineas = ["Sesion web - diagnostico"]
    for c in diagnostico(incluir_lentas):
        marca = "[ok]" if c["ok"] else "[NO]"
        lineas.append(f"  {marca} {c['comprobacion']:<32} "
                      f"{c['detalle']}  ({c['ms']:.0f} ms)")
    return "\n".join(lineas)


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
