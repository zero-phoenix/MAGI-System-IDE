"""
La ronda N empieza sabiendo lo que aprendió la ronda N-1 (P9).

LA MEDICIÓN QUE OBLIGÓ A ESCRIBIR ESTO
======================================
30 de agosto de 2026. Se preparó una ronda de optimización de YabauseVita
partiendo de `PORTING_NOTES.md`, el documento del repositorio que describe el
estado del port. Decía: SH-2 en intérprete puro, vídeo por software, sonido y
mando en DUMMY, ningún juego arranca.

El código real tenía dynarec ARM (`SH2DynARM`), carga de CHD, audio en hilo
dedicado y un renderizador con GPU. Tres juegos arrancaban y se jugaban.

Las tres propuestas de mejora que salieron de ahí eran inútiles: una proponía
sustituir el despacho del intérprete por una tabla de saltos, en un sistema que
lleva un recompilador desde hace semanas. **Nadie mintió; el documento
simplemente había dejado de ser cierto y nadie lo marcó.**

Ese fallo no se arregla leyendo mejor. Se arregla teniendo un documento cuyo
contrato sea acumular en vez de describir, y haciendo que el enjambre lo lea
antes de proponer.

QUÉ HACE ESTE MÓDULO
====================
Cuando el encargo trata de optimizar el emulador, inyecta ARRIBA del prompt las
dos secciones de la bitácora que caducan peor si se olvidan:

  - el **conocimiento acumulado**: lo que ya se midió, con su origen
  - las **reglas derivadas**: lo que ya se intentó y no hay que repetir

Y deja constancia de que se inyectaron, para que «volvió a proponer lo mismo»
deje de ser invisible.

QUÉ NO HACE
===========
No resume la bitácora ni la interpreta. Un resumen generado es exactamente el
mecanismo que produjo `PORTING_NOTES.md`: un texto que fue cierto. Se copian las
secciones tal cual, o no se copia nada.

No escribe rondas. Registrar el resultado es trabajo de Casper al cerrar, con la
medición delante, y va en un commit junto al cambio que la forzó.
"""
from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path

__all__ = ["pertinente", "localizar", "secciones", "para_el_prompt", "citada"]

#: Nombre fijo. Si algún día hay más de una bitácora, se parametriza; hoy
#: inventar la parametrización sería resolver un problema que no existe.
NOMBRE = "BITACORA-OPTIMIZACION.md"

#: Encabezados que se copian, en este orden. Son los que contienen decisiones
#: ya pagadas con mediciones; el resto de la bitácora es contexto reconstruible.
#:
#: La §2 entró tarde y por una comprobación, no por diseño: la primera versión
#: llevaba solo hallazgos, reglas y criterio, y al probarla contra la bitácora
#: real se vio que el enjambre recibía las prohibiciones sin recibir el marco
#: que le dice de qué tres formas se puede atacar el problema. Prohibir sin
#: encuadrar produce propuestas tímidas, no propuestas mejores.
SECCIONES = ("2.", "5.1", "5.2", "3.")


def _plano(s: str) -> str:
    sin = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in sin if not unicodedata.combining(c))


_ENCARGO = re.compile(
    r"\b(yabause|yabausevita|saturn|vidgpu|composite|dynarec|"
    r"optimiz\w*|rendimiento|fps|ronda\s*\d)\b"
)


def pertinente(encargo: str) -> bool:
    """¿Este encargo cae dentro del ciclo que la bitácora gobierna?"""
    return bool(_ENCARGO.search(_plano(encargo)))


def localizar(inicio: str | os.PathLike | None = None) -> Path | None:
    """
    Dónde está la bitácora.

    Orden deliberado: la variable de entorno gana, porque es la única forma de
    que una prueba apunte a un fichero de mentira sin tocar el disco real.
    """
    env = os.environ.get("MAGI_BITACORA")
    if env and Path(env).is_file():
        return Path(env)

    base = Path(inicio or os.getcwd()).resolve()
    for carpeta in (base, *base.parents):
        cand = carpeta / "docs" / NOMBRE
        if cand.is_file():
            return cand
    return None


def secciones(texto: str, cuales: tuple[str, ...] = SECCIONES) -> str:
    """
    Recorta las secciones pedidas por su número de encabezado.

    Copia literal. Un `###` corta un `###`, y un `##` corta cualquier cosa: si
    la bitácora cambia de forma, esto devuelve de menos, nunca de más. Perder
    una sección se nota al leer el prompt; inventarla no se nota nunca.
    """
    lineas = texto.splitlines()
    fuera: list[str] = []
    for numero in cuales:
        nivel = None
        for i, linea in enumerate(lineas):
            m = re.match(r"^(#{2,4})\s*" + re.escape(numero), linea)
            if not m:
                continue
            nivel = len(m.group(1))
            bloque = [linea]
            for siguiente in lineas[i + 1:]:
                m2 = re.match(r"^(#{2,4})\s", siguiente)
                if m2 and len(m2.group(1)) <= nivel:
                    break
                bloque.append(siguiente)
            fuera.append("\n".join(bloque).rstrip())
            break
    return "\n\n".join(fuera)


def para_el_prompt(encargo: str, inicio: str | os.PathLike | None = None) -> str:
    """
    El aviso que va ARRIBA del prompt.

    Si no hay bitácora se devuelve cadena vacía en vez de una advertencia: un
    aviso de que falta un fichero, repetido en cada encargo, se convierte en
    ruido y acaba tapando los avisos que sí importan.
    """
    if not pertinente(encargo):
        return ""
    ruta = localizar(inicio)
    if ruta is None:
        return ""
    try:
        cuerpo = secciones(ruta.read_text(encoding="utf-8"))
    except OSError:
        return ""
    if not cuerpo.strip():
        return ""
    return (
        "\n\nLO QUE YA SE MIDIÓ. Este encargo pertenece a un ciclo con "
        f"bitácora ({ruta.name}). Antes de proponer nada, lee esto:\n\n"
        f"{cuerpo}\n\n"
        "Una propuesta que choca con una regla derivada se rechaza sin llegar "
        "a compilar, y hay que decir con qué regla choca. Repetir un intento "
        "ya descartado no es una propuesta: es olvido con formato de idea.\n"
        "Si tu propuesta contradice un hallazgo, dilo y trae la medición que "
        "lo desmiente — la bitácora se corrige con datos, no por omisión."
    )


def citada(texto: str) -> list[str]:
    """
    Qué identificadores de la bitácora (A1, R4...) se nombran en lo entregado.

    Es la métrica equivalente a `menciones` de la caja de herramientas: hace
    visible el caso «tenía el hallazgo delante y propuso lo contrario».
    """
    return list(dict.fromkeys(re.findall(r"\b([AR]\d{1,2})\b", texto or "")))
