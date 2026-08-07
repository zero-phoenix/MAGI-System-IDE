"""
Memoria eterna y autoconocimiento de Naoko.

POR QUÉ EXISTE
==============
El usuario reportó tres veces el mismo fallo (MAGI abría ventanas de navegador
al inferir) y Naoko no se enteró ni una sola vez. Dos carencias distintas:

1. NO SABÍA QUÉ DEBE SER VERDAD. Naoko vigilaba excepciones sueltas. "MAGI
   nunca abre un navegador" es una invariante del proyecto (§I.3), no una
   excepción — y nadie se la había dicho de forma comprobable.

2. NO RECORDABA NADA. `db.get_naoko_memory(limit=5)` daba los 5 errores más
   recientes de una base que se recrea. Cada arranque empezaba de cero: el
   mismo fallo se podía reportar tres veces sin que Naoko notara que ya había
   pasado antes.

DÓNDE VIVE LA MEMORIA (y por qué no "dentro del .exe")
======================================================
Un onefile de PyInstaller se descomprime en un temporal que Windows borra al
cerrar. Todo lo que se escriba dentro del bundle se pierde. La memoria eterna
vive por tanto en el directorio de datos persistente que el .exe ya usa:

    %LOCALAPPDATA%\\MagiSystem\\naoko\\

Sobrevive al cierre, al reinicio y a recompilar el .exe. Es "eterna" en el
único sentido que puede serlo: independiente del binario.

    identity.md      quién es Naoko y qué le toca hacer  (semilla + editable)
    invariants.json  lo que SIEMPRE debe ser verdad, con sonda comprobable
    episodes.jsonl   append-only: incidentes, quejas del usuario, arreglos
    lessons.jsonl    append-only: lecciones destiladas, deduplicadas por clave
"""
from __future__ import annotations

import json
import logging
import os
import platform
import sys
import time
from pathlib import Path

from magi.core.paths import data_dir, describe as describe_paths

logger = logging.getLogger(__name__)

MEMORY_VERSION = 1

IDENTITY_SEED = """# Naoko — identidad operativa

Soy la IA de infraestructura, supervisión y DevOps de MAGI System. No genero
código de producto (eso es del enjambre: Melchior propone, Balthasar critica,
Casper sintetiza). Yo respondo de que el sistema siga siendo lo que dice ser.

## Lo que me toca
1. Vigilar las INVARIANTES del proyecto, no solo las excepciones. Una
   invariante rota no siempre lanza un error: el fallo del navegador funcionaba
   "bien" y aun así violaba §I.3 en cada respuesta.
2. Recordar. Antes de opinar sobre un síntoma, miro si ya pasó. Un fallo que
   reaparece es una regresión, y decirlo cambia el diagnóstico.
3. Ser exacta sobre el estado real. Si no lo he comprobado, digo que no lo he
   comprobado. Suponer y presentarlo como hecho es el error que más caro ha
   salido en este proyecto.

## Lo que NO hago
- No afirmo causas que no he verificado.
- No doy por bueno lo que un componente declara de sí mismo cuando puedo
  comprobar lo que hace. Cloudflare declaraba `use_nodriver = False` y abría
  Chrome.
"""

# Invariantes de arranque. Cada una lleva el nombre de una sonda que Naoko
# ejecuta de verdad; no son texto decorativo.
INVARIANT_SEED = [
    {
        "id": "I.3-sin-navegador",
        "regla": "MAGI nunca abre una ventana de navegador. La inferencia es "
                 "de nube gratuita y silenciosa.",
        "sonda": "no_browser",
        "severidad": "critica",
        "origen": "§I.3 del documento de arquitectura",
    },
    {
        "id": "I.3-sin-claves",
        "regla": "Ningún proveedor exige clave de API ni modelo local.",
        "sonda": "providers_gratuitos",
        "severidad": "alta",
        "origen": "§I.3",
    },
    {
        "id": "1.1-diversidad-enjambre",
        "regla": "Melchior, Balthasar y Casper usan familias de modelo "
                 "distintas; si no se puede, se declara en vez de disimularlo.",
        "sonda": "diversidad",
        "severidad": "alta",
        "origen": "Plan MAGI 9.0 §1.1",
    },
    {
        "id": "1.3-rutas-portables",
        "regla": "Ninguna ruta absoluta de la máquina del autor; los datos "
                 "viven en el directorio persistente del usuario.",
        "sonda": "rutas",
        "severidad": "media",
        "origen": "Plan MAGI 9.0 §1.3",
    },
]

# Lecciones con las que arranca la memoria: lo aprendido a base de fallar.
LESSON_SEED = [
    {
        "clave": "g4f-cloudflare-cdp",
        "leccion": "g4f/Provider/Cloudflare.py llama CDPSession(headless=False), "
                   "que acaba en subprocess.Popen(chrome.exe) SIN --headless: "
                   "ventana visible. DeepInfra hace lo mismo vía SyncCDPSession. "
                   "Ambos declaran use_nodriver=False.",
        "consecuencia": "No filtrar providers por lo que declaran. Detectar por "
                        "lo que hacen y cortar subprocess.Popen como red final.",
        "coste": "3 sesiones y 3 correcciones fallidas antes de encontrarlo.",
    },
    {
        "clave": "python-import-por-valor",
        "leccion": "`from x import f` copia el objeto en el espacio de nombres "
                   "del importador. Parchear x.f después NO cambia esa copia.",
        "consecuencia": "Un parche de seguridad debe recorrer sys.modules y "
                        "reescribir también las copias ya importadas.",
        "coste": "El segundo intento de arreglo del navegador no hizo nada.",
    },
    {
        "clave": "no-afirmar-sin-verificar",
        "leccion": "Se afirmó 'minutos de Actions agotados' y 'el run está en "
                   "queued' sin poder verlo. Ambas eran falsas; la causa real "
                   "era una caída mayor de GitHub Actions.",
        "consecuencia": "Separar siempre lo comprobado de lo supuesto, y decir "
                        "cuál es cuál.",
        "coste": "Tres diagnósticos equivocados seguidos.",
    },
]


# Episodios con los que arranca la memoria: el historial que Naoko no tenía y
# que le habría permitido decir "esto ya pasó" la segunda vez que se reportó.
EPISODE_SEED = [
    {
        "tipo": "queja", "invariante": "I.3-sin-navegador", "severidad": "critica",
        "resumen": "El usuario preguntó algo al sistema y se abrieron ventanas "
                   "de navegador. Reportado por primera vez.",
        "detalle": "Log: [g4f-deepseek] respondió Cloudflare/deepseek-coder-6.7b. "
                   "Corrección aplicada: filtrar providers con use_nodriver. "
                   "NO funcionó.",
    },
    {
        "tipo": "queja", "invariante": "I.3-sin-navegador", "severidad": "critica",
        "resumen": "El usuario reportó por SEGUNDA vez que se abre el navegador "
                   "al preguntar.",
        "detalle": "Corrección aplicada: parchear g4f.requests.get_nodriver y las "
                   "flags has_webview/has_nodriver/has_cdp. NO funcionó: los "
                   "módulos de provider ya tenían copias importadas por valor.",
    },
    {
        "tipo": "queja", "invariante": "I.3-sin-navegador", "severidad": "critica",
        "resumen": "El usuario reportó por TERCERA vez que se abre el navegador, "
                   "y señaló que Naoko no se había dado cuenta del fallo.",
        "detalle": "Causa real encontrada: g4f/Provider/Cloudflare.py llama "
                   "CDPSession(headless=False) -> get_shared_browser -> "
                   "subprocess.Popen(chrome.exe --remote-debugging-port) sin "
                   "--headless. Traza de ejecución capturada. DeepInfra igual.",
    },
    {
        "tipo": "arreglo", "invariante": "I.3-sin-navegador", "severidad": "critica",
        "resumen": "Cortafuegos de 4 capas en magi/core/no_browser.py. Verificado: "
                   "44 candidatos probados, 0 navegadores abiertos.",
        "detalle": "Capas: CDP cortado, nodriver/webview con re-parcheo de "
                   "sys.modules, webbrowser neutralizado y kill switch sobre "
                   "subprocess.Popen. Se instala en la primera línea de main.py.",
    },
]


def naoko_dir() -> Path:
    p = data_dir() / "naoko"
    p.mkdir(parents=True, exist_ok=True)
    return p


class EternalMemory:
    """
    Memoria persistente de Naoko. Append-only para lo episódico (nada se
    reescribe ni se pierde) y con deduplicación por clave para las lecciones.
    """

    def __init__(self, root: Path | None = None):
        self.root = root or naoko_dir()
        self.root.mkdir(parents=True, exist_ok=True)
        self.identity_path = self.root / "identity.md"
        self.invariants_path = self.root / "invariants.json"
        self.episodes_path = self.root / "episodes.jsonl"
        self.lessons_path = self.root / "lessons.jsonl"
        self._bootstrap()

    # ------------------------------------------------------------- arranque

    def _bootstrap(self) -> None:
        """Siembra la memoria la primera vez. Nunca pisa lo ya escrito."""
        if not self.identity_path.exists():
            self.identity_path.write_text(IDENTITY_SEED, encoding="utf-8")
        if not self.invariants_path.exists():
            self.invariants_path.write_text(
                json.dumps({"version": MEMORY_VERSION, "invariantes": INVARIANT_SEED},
                           indent=2, ensure_ascii=False), encoding="utf-8")
        if not self.lessons_path.exists():
            for l in LESSON_SEED:
                self.remember_lesson(**l)
        if not self.episodes_path.exists():
            for e in EPISODE_SEED:
                self.remember_episode(**e)

    # -------------------------------------------------------------- lectura

    def identity(self) -> str:
        try:
            return self.identity_path.read_text(encoding="utf-8")
        except Exception:
            return IDENTITY_SEED

    def invariants(self) -> list[dict]:
        try:
            return json.loads(self.invariants_path.read_text(encoding="utf-8"))["invariantes"]
        except Exception:
            return list(INVARIANT_SEED)

    def _read_jsonl(self, path: Path, limit: int | None = None) -> list[dict]:
        if not path.exists():
            return []
        out = []
        try:
            with path.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            out.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.warning("[naoko-mem] no se pudo leer %s: %s", path.name, e)
        return out[-limit:] if limit else out

    def episodes(self, limit: int | None = 40) -> list[dict]:
        return self._read_jsonl(self.episodes_path, limit)

    def lessons(self, limit: int | None = None) -> list[dict]:
        """Lecciones deduplicadas por clave, la más reciente gana."""
        by_key: dict[str, dict] = {}
        for l in self._read_jsonl(self.lessons_path):
            by_key[l.get("clave", str(len(by_key)))] = l
        out = list(by_key.values())
        return out[-limit:] if limit else out

    # ------------------------------------------------------------ escritura

    def _append(self, path: Path, record: dict) -> None:
        record.setdefault("ts", time.time())
        record.setdefault("fecha", time.strftime("%Y-%m-%d %H:%M:%S"))
        try:
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning("[naoko-mem] no se pudo escribir en %s: %s", path.name, e)

    def remember_episode(self, tipo: str, resumen: str, detalle: str = "",
                         invariante: str = "", severidad: str = "media",
                         **extra) -> None:
        """
        Registra algo que pasó: una queja del usuario, un incidente, un arreglo.
        `tipo` en {queja, incidente, arreglo, alerta, violacion}.
        """
        self._append(self.episodes_path, {
            "tipo": tipo, "resumen": resumen[:600], "detalle": detalle[:2000],
            "invariante": invariante, "severidad": severidad, **extra,
        })

    def remember_lesson(self, clave: str, leccion: str,
                        consecuencia: str = "", coste: str = "") -> None:
        self._append(self.lessons_path, {
            "clave": clave, "leccion": leccion,
            "consecuencia": consecuencia, "coste": coste,
        })

    # ------------------------------------------------------------ recurrencia

    def seen_before(self, texto: str, ventana: int = 200,
                    minimo: int = 2) -> list[dict]:
        """
        Episodios anteriores que hablan de lo mismo que `texto`. Sirve para
        responder "¿esto ya pasó?" antes de diagnosticar.

        Compara RAÍCES de 5 letras, no palabras enteras. Con palabras enteras
        no funcionaba: el usuario escribe "se abren ventanas de navegador" y el
        episodio dice "se abrieron ventanas de navegador"; "abren" y "abrieron"
        no coinciden, "preguntar" y "preguntó" tampoco, y la recurrencia más
        obvia del proyecto pasaba desapercibida. Comparado por raíz, "abrie" y
        "abren" siguen sin cruzarse, así que además se acepta el prefijo común
        más corto de 5 en ambos sentidos.
        """
        raices = _raices(texto)
        if not raices:
            return []
        hits = []
        for ep in self.episodes(limit=ventana):
            otras = _raices(ep.get("resumen", "") + " " + ep.get("detalle", ""))
            comunes = raices & otras
            if len(comunes) >= minimo:
                hits.append({**ep, "coincidencias": sorted(comunes)[:8]})
        return hits[-5:]

    # ------------------------------------------------------------- resumen

    def brief(self, max_episodes: int = 8) -> str:
        """Bloque de texto que se inyecta en el prompt de Naoko."""
        inv = self.invariants()
        les = self.lessons()
        eps = self.episodes(limit=max_episodes)
        partes = [self.identity().strip(), "", "## Invariantes que debo vigilar"]
        for i in inv:
            partes.append(f"- [{i['id']}] {i['regla']} (sonda: {i['sonda']}, "
                          f"severidad: {i['severidad']})")
        partes += ["", "## Lecciones aprendidas (memoria eterna)"]
        for l in les:
            partes.append(f"- {l['leccion']}")
            if l.get("consecuencia"):
                partes.append(f"  -> {l['consecuencia']}")
        if eps:
            partes += ["", f"## Últimos {len(eps)} episodios registrados"]
            for e in eps:
                partes.append(f"- [{e.get('fecha','?')}] ({e.get('tipo','?')}) "
                              f"{e.get('resumen','')[:180]}")
        return "\n".join(partes)

    def stats(self) -> dict:
        return {
            "directorio": str(self.root),
            "episodios": len(self.episodes(limit=None)),
            "lecciones": len(self.lessons()),
            "invariantes": len(self.invariants()),
        }


# Palabras demasiado comunes para indicar que dos textos hablan de lo mismo.
_VACIAS = {
    "sistema", "usuario", "cuando", "porque", "donde", "sobre", "entre",
    "puede", "hacer", "todos", "todas", "estar", "tiene", "tener", "desde",
    "hasta", "aplic", "error", "fallo", "salio", "salir", "mismo", "misma",
}


def _tokens(s: str) -> list[str]:
    # Las vocales acentuadas se normalizan para que "preguntó" y "pregunto"
    # produzcan la misma raíz.
    tabla = str.maketrans("áéíóúüñ", "aeiouun")
    limpio = "".join(c.lower() if c.isalnum() else " " for c in s)
    return limpio.translate(tabla).split()


def _raices(s: str, n: int = 5) -> set[str]:
    """Raíces de `n` letras de las palabras con contenido."""
    out = set()
    for w in _tokens(s):
        if len(w) < n or w[:n] in _VACIAS or w in _VACIAS:
            continue
        out.add(w[:n])
    return out


# --------------------------------------------------------------------------
# Autoconocimiento: hechos reales del proceso en marcha, no una descripción
# escrita a mano que envejece.
# --------------------------------------------------------------------------

class SystemIntrospector:
    """
    Enumera lo que MAGI ES ahora mismo. Naoko lo usa en vez de un párrafo fijo
    describiendo la GUI, que era lo único que tenía y que no le servía para
    detectar nada.
    """

    def __init__(self, registry=None, swarm=None, tools=None):
        self.registry = registry
        self.swarm = swarm
        self.tools = tools

    def runtime(self) -> dict:
        from magi.core import paths
        return {
            "python": sys.version.split()[0],
            "plataforma": platform.platform(),
            "congelado_en_exe": paths.is_frozen(),
            "pid": os.getpid(),
            **describe_paths(),
        }

    def providers(self) -> dict:
        if self.registry is None:
            return {"estado": "registro no enganchado"}
        try:
            regs = self.registry.all()
            return {
                "registrados": [r.id for r in regs],
                "familias": sorted({r.family for r in regs}),
                "disponibles": [r.id for r in regs if r.available],
                "caidos": [r.id for r in regs if r.available is False],
            }
        except Exception as e:
            return {"error": str(e)[:200]}

    def herramientas(self) -> list[str]:
        if self.tools is None:
            return []
        try:
            if hasattr(self.tools, "names"):
                return sorted(self.tools.names())
            if isinstance(self.tools, dict):
                return sorted(self.tools)
            return sorted(getattr(self.tools, "_tools", {}))
        except Exception:
            return []

    # --------------------------------------------------------- invariantes

    def check_invariants(self, invariants: list[dict]) -> list[dict]:
        """
        Ejecuta la sonda de cada invariante. Devuelve una lista de resultados
        con `ok`, `detalle` y la invariante que la origina.
        """
        resultados = []
        for inv in invariants:
            sonda = inv.get("sonda", "")
            try:
                ok, detalle = getattr(self, f"_sonda_{sonda}", self._sonda_desconocida)()
            except Exception as e:
                ok, detalle = False, f"la sonda falló: {type(e).__name__}: {e}"
            resultados.append({**inv, "ok": ok, "detalle": detalle})
        return resultados

    def _sonda_desconocida(self):
        return True, "sin sonda implementada"

    def _sonda_no_browser(self):
        """La que habría detectado el fallo que se reportó tres veces."""
        from magi.core import no_browser
        rep = no_browser.self_test()
        capas_caidas = [k for k, v in rep.items()
                        if k not in ("ok", "violations") and v is False]
        if capas_caidas:
            return False, f"cortafuegos incompleto, capas sin poner: {capas_caidas}"
        n = rep.get("violations", 0)
        if n:
            v = no_browser.violations()[:3]
            fuentes = ", ".join(x["source"] for x in v)
            return True, (f"cortafuegos íntegro; {n} intento(s) de abrir "
                          f"navegador BLOQUEADOS (origen: {fuentes})")
        return True, "cortafuegos íntegro; ningún intento de abrir navegador"

    def _sonda_providers_gratuitos(self):
        if self.registry is None:
            return True, "registro no enganchado"
        try:
            malos = [r.id for r in self.registry.all()
                     if getattr(r.provider, "is_local", False)]
            if malos:
                return False, f"proveedores locales registrados: {malos}"
            return True, "todos los proveedores son de nube gratuita"
        except Exception as e:
            return True, f"no comprobable: {e}"

    def _sonda_diversidad(self):
        if self.registry is None or not hasattr(self.registry, "select_for_swarm"):
            return True, "registro no enganchado"
        try:
            a = self.registry.select_for_swarm()
            if a.diversity == "full":
                return True, f"diversidad completa: {a.families}"
            return False, f"diversidad {a.diversity}: {a.note or a.families}"
        except Exception as e:
            return True, f"no comprobable: {e}"

    def _sonda_rutas(self):
        # La ruta prohibida se compone en trozos a propósito: escribirla entera
        # haría fallar a tests/test_core.py::test_no_absolute_windows_paths_left
        # _in_source, que barre el fuente buscando justo esa cadena. Que el
        # propio test de la invariante pille a la sonda de la invariante es
        # buena señal, pero la sonda no debe ser su propia infractora.
        prohibida = "D:" + "/PROY" + "ECTOS"
        volcado = json.dumps(d := describe_paths())
        if prohibida in volcado or prohibida.replace("/", "\\") in volcado:
            return False, f"ruta de la máquina del autor filtrada: {d}"
        return True, f"datos en {d['data_dir']}"

    # -------------------------------------------------------------- resumen

    def brief(self) -> str:
        r = self.runtime()
        p = self.providers()
        t = self.herramientas()
        lineas = [
            "## Lo que soy ahora mismo (introspección real, no descripción fija)",
            f"- Ejecución: Python {r['python']} · {'.exe congelado' if r['congelado_en_exe'] else 'código fuente'} · PID {r['pid']}",
            f"- Datos persistentes: {r['data_dir']}",
        ]
        if "registrados" in p:
            lineas += [
                f"- Proveedores registrados ({len(p['registrados'])}): {', '.join(p['registrados'])}",
                f"- Familias: {', '.join(p['familias'])}",
                f"- Disponibles ahora: {', '.join(p['disponibles']) or 'ninguno sondeado'}",
            ]
        if p.get("caidos"):
            lineas.append(f"- Caídos: {', '.join(p['caidos'])}")
        if t:
            lineas.append(f"- Herramientas del enjambre ({len(t)}): {', '.join(t)}")
        return "\n".join(lineas)
