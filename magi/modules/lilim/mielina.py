"""
VAINA DE MIELINA — Acelerador neuro-computacional de MAGI (megaplan v13).

METÁFORA BIOLÓGICA Y FUNCIÓN
============================
En el sistema nervioso, la mielina envuelve los axones para permitir la
conducción saltatoria (transmisión hasta 100 veces más veloz).

En MAGI, Lilim actúa como la vaina de mielina: una capa local ultrarrápida
(Qwen 2.5 1.5B Instruct en KoboldCpp + memoria EPD) que envuelve a:
  - MELCHIOR:  Especulación y andamiaje preliminar (<250 ms) antes de la nube.
  - BALTHASAR: Pre-auditoría local y chequeo estático de defectos obvios.
  - CASPER:    Destilación y compresión de contexto de debates extensos.
  - NAOKO:     Visión multimodal local para inspección de capturas web/DOM.
  - RITSUKO:   Enrutamiento semántico instantáneo y caché sin latencia.
"""
from __future__ import annotations

import ast
import logging
import re
from pathlib import Path
from typing import Any

from .cliente_kobold import ClienteKobold
from .rapida import hechos_de_imagen

logger = logging.getLogger(__name__)

_cliente_singleton: ClienteKobold | None = None


def obtener_cliente() -> ClienteKobold:
    """Devuelve el cliente singleton de KoboldCpp."""
    global _cliente_singleton
    if _cliente_singleton is None:
        _cliente_singleton = ClienteKobold()
    return _cliente_singleton


async def lubricar_propuesta(encargo: str, contexto: str = "") -> str | None:
    """
    Genera un andamio o esqueleto de código preliminar para Melchior.

    Permite que Melchior reciba una estructura sólida de partida, reduciendo
    el consumo de tokens y el tiempo de respuesta del proveedor de nube.
    """
    cliente = obtener_cliente()
    if not await cliente.esta_disponible(timeout=0.8):
        return None

    prompt = (
        f"Actúa como un arquitecto de software de alto rendimiento.\n"
        f"Encargo: {encargo}\n"
        f"Contexto previo: {contexto[:400] if contexto else 'Ninguno'}\n\n"
        f"Genera EXCLUSIVAMENTE el esqueleto técnico o andamio en código limpio "
        f"(Python o C según aplique), con firmas de funciones, contratos y "
        f"estructuras de datos bien definidas. Sé conciso."
    )
    return await cliente.generar(prompt, max_tokens=380, temperature=0.15, timeout=12.0)


#: Bloques cercados de Markdown: ```lenguaje ... ```
_CERCA = re.compile(r"```([A-Za-z0-9_+#-]*)[ \t]*\r?\n(.*?)```", re.S)

#: Etiquetas de cerca que significan «esto es Python».
_ETIQUETAS_PY = {"python", "py", "python3"}

#: Señales de que un texto SIN cercas es Python de verdad. Se exige que
#: alguna aparezca a principio de línea: `import` dentro de una frase en
#: prosa no convierte la frase en código.
_SENAL_PY = re.compile(
    r"^[ \t]*(def |async def |class |import |from \w+ import |@\w+)",
    re.M)

#: Señales de que NO lo es. `#include` y las llaves delatan a C/C++, que es
#: el 100 % del emulador y la mitad de lo que este enjambre revisa.
_SENAL_NO_PY = re.compile(
    r"^[ \t]*#\s*include\b|^[ \t]*(?:static|typedef|unsigned|void|struct)\s|"
    r"[;{}][ \t]*$", re.M)


def _parece_python(texto: str) -> bool:
    """
    ¿Este texto sin cercas es Python ROTO, o simplemente no es Python?

    Solo se pregunta cuando `ast.parse` ya ha fallado, y esa distinción es
    todo el arreglo: un `SyntaxError` sobre código C no es un defecto del
    código, es un defecto del auditor.

    La primera versión de esta heurística exigía `def`/`class`/`import` a
    principio de línea y silenciaba un `try/except` suelto, que es Python
    perfectamente válido. Por eso ahora el parseo va PRIMERO: lo que compila
    es Python y no hace falta adivinarlo. Aquí solo llega lo que no compila.
    """
    return bool(_SENAL_PY.search(texto)) and not _SENAL_NO_PY.search(texto)


def _fragmentos_python(texto: str) -> list[str]:
    """
    Lo que de este texto SÍ se puede auditar con el `ast` de Python.

    Melchior no devuelve código desnudo: devuelve prosa con bloques
    cercados, y a menudo en C. Pasar todo eso a `ast.parse` producía un
    `SyntaxError en línea 1` — medido — en CADA propuesta real. Balthasar
    recibía un defecto inventado y gastaba su turno en él.
    """
    cercas = _CERCA.findall(texto)
    if cercas:
        fuera = []
        for etiqueta, cuerpo in cercas:
            eti = etiqueta.strip().lower()
            if eti in _ETIQUETAS_PY:
                fuera.append(cuerpo)
            elif not eti and _compila(cuerpo):
                # Cerca sin etiqueta: solo cuenta si de verdad compila como
                # Python. Adivinar el lenguaje es lo que causó el fallo.
                fuera.append(cuerpo)
        return fuera

    # Sin cercas. Si compila, es Python y no hay nada que adivinar; si no
    # compila, hay que decidir si es Python roto (defecto real) o cualquier
    # otro lenguaje (silencio).
    if _compila(texto) or _parece_python(texto):
        return [texto]
    return []


def _compila(texto: str) -> bool:
    try:
        ast.parse(texto)
    except (SyntaxError, ValueError):
        return False
    return True


def pre_auditoria_estatica(codigo: str) -> list[str]:
    """
    Inspección estática determinista para asistir a Balthasar.

    SOLO habla de Python, y solo cuando está seguro de que lo es. Sobre
    cualquier otra cosa **calla**: una objeción fabricada es peor que el
    silencio, porque Balthasar la defiende y el debate se va detrás de ella.
    """
    if not codigo or not codigo.strip():
        return ["Código vacío o ausente"]

    defectos: list[str] = []
    for fragmento in _fragmentos_python(codigo):
        defectos.extend(_defectos_de_un_fragmento(fragmento))
    return defectos


def _defectos_de_un_fragmento(codigo: str) -> list[str]:
    defectos: list[str] = []
    try:
        arbol = ast.parse(codigo)
    except SyntaxError as err:
        return [f"SyntaxError en línea {err.lineno}: {err.msg}"]
    except Exception as err:  # noqa: BLE001 - se REPORTA, no se traga
        # Antes esto era `except Exception: pass`, que es exactamente el
        # defecto que esta función audita dos líneas más abajo. Y era peor
        # que irónico: al fallar por dentro devolvía «sin defectos», que es
        # un verde falso justo donde se decide si hay que criticar.
        logger.warning("[mielina] la pre-auditoría falló: %s", err)
        return [f"Pre-auditoría no concluyente ({type(err).__name__}): "
                f"trátala como SIN COMPROBAR, no como código limpio."]

    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Se ignora el docstring: `def f():\n "doc"\n pass` está tan sin
            # implementar como el que solo lleva `pass`.
            cuerpo = [n for n in nodo.body
                      if not (isinstance(n, ast.Expr)
                              and isinstance(n.value, ast.Constant)
                              and isinstance(n.value.value, str))]
            if len(cuerpo) == 1 and isinstance(cuerpo[0], ast.Pass):
                defectos.append(
                    f"Función '{nodo.name}' solo contiene 'pass' sin implementar.")
        elif isinstance(nodo, ast.Try):
            for handler in nodo.handlers:
                if handler.type is None:
                    defectos.append(
                        "Uso de 'except:' desnudo sin atrapar excepción específica.")
    return defectos


async def lubricar_critica(
    propuesta: str, ejes: list[str] | None = None
) -> list[str]:
    """
    Pre-auditoría rápida para Balthasar.
    Combina escaneo estático local con evaluación neural si KoboldCpp está activo.
    """
    defectos = pre_auditoria_estatica(propuesta)

    cliente = obtener_cliente()
    if await cliente.esta_disponible(timeout=0.8):
        ejes_txt = ", ".join(ejes) if ejes else "seguridad, rendimiento, coherencia"
        prompt = (
            f"Como crítico técnico implacable, evalúa la siguiente propuesta bajo "
            f"los ejes: {ejes_txt}.\n"
            f"Propuesta:\n{propuesta[:1200]}\n\n"
            f"Lista hasta 3 objeciones o defectos técnicos severos en viñetas cortas. "
            f"Si el código es óptimo, responde exactamente: SIN OBJECIONES."
        )
        res = await cliente.generar(prompt, max_tokens=200, temperature=0.1, timeout=10.0)
        if res and "SIN OBJECIONES" not in res.upper():
            for linea in res.splitlines():
                ln = linea.strip("- *").strip()
                if ln and len(ln) > 10:
                    defectos.append(ln)

    return defectos[:5]


async def lubricar_arbitraje(
    encargo: str, propuesta: str, objeciones: list[str]
) -> str | None:
    """
    Destila y comprime el debate para Casper.
    Reduce un contexto extenso a una síntesis ejecutiva de alta densidad.
    """
    cliente = obtener_cliente()
    if not await cliente.esta_disponible(timeout=0.8):
        return None

    obs_txt = "\n".join(f"- {o}" for o in objeciones) if objeciones else "Ninguna objeción mayor."
    prompt = (
        f"Encargo original: {encargo[:300]}\n"
        f"Propuesta de Melchior (extracto):\n{propuesta[:1000]}\n"
        f"Objeciones de Balthasar:\n{obs_txt[:600]}\n\n"
        f"Como árbitro neutral (Casper), resume en un párrafo denso: "
        f"1. Si la propuesta satisface el encargo. "
        f"2. Si las objeciones son bloqueantes o subsanables. "
        f"3. Veredicto recomendado (APROBAR / RECHAZAR / AJUSTAR)."
    )
    return await cliente.generar(prompt, max_tokens=220, temperature=0.1, timeout=10.0)


async def lubricar_vision(
    imagen: bytes | str | Path, instruccion: str = "Describe los elementos interactivos"
) -> dict[str, Any]:
    """
    Análisis multimodal local para Naoko (navegación y percepción visual).
    Extrae hechos deterministas y añade descripción VLM si KoboldCpp está activo.
    """
    info: dict[str, Any] = {}
    if isinstance(imagen, (str, Path)):
        info = hechos_de_imagen(imagen)
    else:
        info = {"formato": "bytes", "tamano": len(imagen)}

    cliente = obtener_cliente()
    if await cliente.esta_disponible(timeout=0.8):
        desc = await cliente.vision(instruccion, imagen, max_tokens=300, timeout=15.0)
        if desc:
            info["analisis_vlm"] = desc
            info["motor_vision"] = "qwen-vlm-local"
    return info


def clasificar_intencion_local(texto: str) -> str:
    """
    Enrutamiento semántico ultraveloz (0 ms):
      - 'memoria_epd': Respuestas instantáneas curadas de Lilim.
      - 'comando_directo': Ejecución de orden / CLI.
      - 'deliberacion_enjambre': Tareas complejas de programación y diseño.
    """
    t = texto.strip().lower()
    if not t:
        return "vacio"
    if t.startswith(("/", "run ", "git ", "python ", "npm ", "task.cancel")):
        return "comando_directo"
    palabras_epd = ("controles", "decomp", "repos", "novedades", "mando", "vita")
    if any(p in t for p in palabras_epd) and len(t.split()) < 12:
        return "memoria_epd"
    return "deliberacion_enjambre"
