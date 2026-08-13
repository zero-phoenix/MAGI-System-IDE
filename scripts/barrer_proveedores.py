"""
Mide TODOS los proveedores de g4f sin autenticación, uno a uno, y lo escribe.

POR QUÉ EXISTE
==============
El catálogo de MAGI llevaba 13 candidatos. g4f expone 37 con `working=True` y
`needs_auth=False`. Nadie había mirado los otros 24, y así fue como la familia
`claude` figuró meses como «imposible» mientras `Perplexity` —ya en el
catálogo— servía `claude45sonnet` sin cuenta ni cookies.

Este script existe para que esa clase de descuido no dependa de que alguien se
acuerde de mirar.

TRES DECISIONES QUE NO SON OBVIAS
=================================
1. **El prompt NO es «di: funciona».** Ese canario penalizaba a Perplexity, que
   lo interpreta como una búsqueda y contesta «No entiendo la consulta»: el
   mejor proveedor del sistema suspendía por culpa del examen. Se usa una
   pregunta técnica breve con respuesta verificable.

2. **Se anota el IDIOMA de la respuesta.** Yqcloud responde rápido y en chino:
   por latencia gana, por utilidad es inservible. Sin este eje, la medida
   miente por omisión.

3. **Lo PRIMERO es el cortafuegos, y esto lo aprendí rompiendo la regla.**
   La primera versión de este script llamaba a `compat_curl()` y `compat_g4f()`
   pero NO instalaba `no_browser`. Al llegar a `Cloudflare`, g4f hizo lo que
   hace: `CDPSession(headless=False)`. Se abrió una ventana de Chrome titulada
   «AI Playground» en la máquina del usuario — exactamente lo único que este
   proyecto prohíbe.

   Que el sistema tenga el cortafuegos puesto no basta si un script lo esquiva.
   Se instala `no_browser` ANTES de importar g4f, y esa es LA defensa.

   La primera corrección añadió además una segunda capa: saltar los proveedores
   cuyo fuente contiene marcadores de navegador. Salió mal y se quitó. Ese
   detector (`_uses_browser`) busca marcadores en el FUENTE, así que marca
   también al que tiene una ruta con navegador *opcional*: saltó a `Gemini`,
   que responde perfectamente sin abrir nada (medido: 4 879 ms). El sistema
   real usa ese detector para ORDENAR —los sospechosos van los últimos—, no
   para excluir, y hace bien.

   Así que se intenta con todos y manda el cortafuegos: si un proveedor busca
   el navegador, salta `BrowserBlocked` y eso se anota como resultado. Es más
   información y es igual de seguro.

4. **La salida va a un fichero, no a la consola.** Y no es un detalle de
   comodidad: la primera versión de esta medición registró
   `Yqcloud -> UnicodeEncodeError` y estuve a punto de darlo por roto. El error
   lo lanzaba el `print` de la propia sonda al volcar una respuesta con un
   emoji en una consola cp1252. **El instrumento estaba averiado, no el
   proveedor.** Aquí todo se escribe en UTF-8 y nada se imprime sin plegar.

USO
===
    python scripts/barrer_proveedores.py            # todos
    python scripts/barrer_proveedores.py --plazo 30 # con otro plazo
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

# EL CORTAFUEGOS, ARRIBA DEL TODO Y AL IMPORTAR. Ver el punto 3 de la cabecera.
#
# Estaba dentro de `medir()`, antes de la primera llamada, y en ORDEN DE
# EJECUCIÓN eso era correcto. `test_scripts_no_esquivan_el_cortafuegos` lo
# marcó igual, porque compara líneas y no ejecución — y tiene razón: la regla
# «instálalo arriba» se verifica de un vistazo y no se puede equivocar,
# mientras que «instálalo antes de la primera llamada» exige seguir el flujo
# entero cada vez que alguien mueva una función.
#
# Cuando la consecuencia de equivocarse es una ventana abierta en la máquina
# del usuario, la regla verificable de un vistazo gana a la regla lista.
from magi.core.no_browser import install as _instalar_cortafuegos  # noqa: E402

_instalar_cortafuegos()

SALIDA = RAIZ / "barrido-proveedores.json"

#: Pregunta técnica breve, con respuesta verificable y sin ambigüedad. Un
#: proveedor que responde bien a esto sirve para el enjambre; uno que la
#: interpreta como búsqueda web, también (contestará, aunque cite fuentes).
PROMPT = "En una sola frase: ¿qué diferencia hay entre un mutex y un semáforo?"

#: Palabras que delatan que entendió la pregunta, en cualquiera de los idiomas
#: admitidos. No se exige una respuesta concreta —eso sería puntuar el modelo,
#: no su disponibilidad— sino señales de que el tema es el correcto.
SEÑALES = ("mutex", "semáforo", "semaforo", "semaphore", "semaforo",
           "exclusión", "exclusion", "hilo", "thread", "contador", "counter")


def plegar(texto: str) -> str:
    """ASCII imprimible en cualquier consola. Ver el punto 3 de la cabecera."""
    d = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in d if not unicodedata.combining(c)).encode(
        "ascii", "replace").decode("ascii")


def idioma_de(texto: str) -> str:
    from magi.core import idioma
    return idioma.detectar(texto, por_defecto="?")


def candidatos() -> list[tuple[str, str | None]]:
    from g4f.Provider import __providers__

    fuera: list[tuple[str, str | None]] = []
    for p in __providers__:
        try:
            if not getattr(p, "working", False):
                continue
            if getattr(p, "needs_auth", False):
                continue
            nombre = p.__name__
            modelos = list(getattr(p, "models", []) or [])
            por_defecto = getattr(p, "default_model", None)
            # El por defecto siempre; y hasta 3 modelos «interesantes» más, para
            # no gastar media hora en proveedores con 200 modelos.
            elegidos: list[str | None] = [por_defecto]
            for clave in ("claude", "gpt-5", "gpt-4o", "o4-mini", "deepseek-v3",
                          "qwen-3", "llama-3.3", "mistral", "grok"):
                for m in modelos:
                    if clave in str(m).lower() and m not in elegidos:
                        elegidos.append(m)
                        break
                if len(elegidos) >= 4:
                    break
            for m in elegidos:
                fuera.append((nombre, m))
        except Exception:
            continue
    return fuera


def medir(plazo: float) -> list[dict]:
    # El cortafuegos ya está puesto al importar el módulo (ver arriba).
    # `install()` es idempotente, así que se reafirma sin coste: g4f puede
    # haberse cargado por otra vía entre medias.
    _instalar_cortafuegos()

    from magi.core.providers.compat_curl import aplicar as compat_curl
    from magi.core.providers.compat_g4f import aplicar as compat_g4f
    compat_curl()
    compat_g4f()

    import g4f.Provider as GP
    from g4f.client import Client

    cliente = Client()
    filas: list[dict] = []
    lista = candidatos()
    for i, (nombre, modelo) in enumerate(lista, 1):
        clase = getattr(GP, nombre, None)
        if clase is None:
            continue
        t0 = time.perf_counter()
        fila: dict = {"proveedor": nombre, "modelo": modelo}
        try:
            r = cliente.chat.completions.create(
                model=modelo or "", provider=clase,
                messages=[{"role": "user", "content": PROMPT}], timeout=plazo)
            texto = (r.choices[0].message.content or "").strip()
            fila.update({
                "ok": bool(texto),
                "ms": round((time.perf_counter() - t0) * 1000),
                "idioma": idioma_de(texto),
                "entendio": any(s in texto.lower() for s in SEÑALES),
                "muestra": texto[:160],
            })
        except Exception as e:
            fila.update({
                "ok": False,
                "ms": round((time.perf_counter() - t0) * 1000),
                "error": f"{type(e).__name__}: {str(e)[:140]}",
            })
        filas.append(fila)
        # Progreso plegado a ASCII, por el punto 3.
        print(plegar(f"[{i}/{len(lista)}] {nombre}/{modelo} "
                     f"{'OK' if fila.get('ok') else 'no'} "
                     f"{fila['ms']} ms {fila.get('idioma','')}"), flush=True)
    return filas


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plazo", type=float, default=40.0)
    args = ap.parse_args()

    filas = medir(args.plazo)
    vivos = [f for f in filas if f.get("ok")]
    SALIDA.write_text(json.dumps({
        "fecha": time.strftime("%Y-%m-%d"),
        "prompt": PROMPT,
        "total": len(filas),
        "vivos": len(vivos),
        "filas": filas,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(plegar(f"\n{len(vivos)} de {len(filas)} responden -> {SALIDA.name}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
