"""
Trinquete de tamaño para `magi/`: no baja solo, pero no sube.

POR QUÉ AHORA
=============
La interfaz tenía tope desde hace tiempo (`App.tsx < 900 líneas`) y me cazó dos
veces, las dos con razón: obligó a extraer `CodigoMarkdown.tsx` y
`GraficoRondas.tsx`, y el resultado fue mejor.

El núcleo no tenía ninguno. Medido hoy:

    naoko.py                1520 líneas
    agents.py               1044
    kernel.py                954
    g4f_backend.py           892
    sesion_web.py            865

`naoko.py` es SESENTA POR CIENTO más grande que el límite que se le exige a la
interfaz, y nadie lo había notado porque nada lo miraba.

POR QUÉ UN TRINQUETE Y NO UN LÍMITE
===================================
Un límite duro de, digamos, 900 líneas dejaría cinco ficheros en rojo desde el
minuto uno, y un test que nace roto se aprende a ignorar — que es exactamente
cómo se pierde un guardián.

El trinquete parte del tamaño ACTUAL de cada fichero y solo impide que crezca.
Refactorizar baja el techo; no refactorizar no rompe nada. Es el mismo
mecanismo que el detector de huérfanos, y por el mismo motivo: la deuda que ya
existe se paga cuando se pueda, pero la nueva no entra.

CÓMO SE ACTUALIZA
=================
Si un fichero baja de tamaño, se baja su número aquí en el mismo commit. Si un
fichero necesita crecer de verdad —y a veces pasa—, se sube el número Y se
explica por qué en el mensaje del commit. Lo que no puede es crecer en silencio.
"""
from __future__ import annotations

import pathlib

import pytest

RAIZ = pathlib.Path(__file__).resolve().parents[1]

#: Margen sobre el tamaño medido. Un trinquete al milímetro convierte cualquier
#: comentario nuevo en un fallo, y entonces la gente borra comentarios para que
#: pase el test — que es peor código a cambio de un número más bonito.
HOLGURA = 40

#: Tamaño máximo por fichero, medido el 2026-08-13 y redondeado con holgura.
#: Solo se listan los que superan `TECHO_GENERAL`; el resto se rige por él.
TECHOS: dict[str, int] = {
    # +40 en la ejecución del megaplan: C13 —Naoko no diagnostica con la cuota
    # que ella misma está gastando— y la distinción entre «no concluyente» y
    # «deriva». Cuarenta líneas contra cuatro falsos positivos medidos que
    # reordenaban el reparto del enjambre.
    "magi/modules/infrastructure/naoko.py": 1600,
    # +45 en la ejecución del megaplan: la guarda C1 —que el árbitro no firme
    # lo que no ha leído— y el mensaje de entrega sin arbitraje (C2), que trae
    # la tesis y la crítica en vez de tirarlas. Son las líneas que separan
    # «aprobado» de «aprobado sin haber recibido nada».
    # (y +45 más por C3 —techo de iteración desde el presupuesto—, C10
    # —presupuesto de dependencias— y C15 —decir cómo se entendió el encargo—.)
    "magi/modules/swarm/agents.py": 1230,
    # +15 en la ejecución del megaplan: B8, la sonda espera a que el enjambre
    # esté quieto en vez de medir la cuota que la tarea acaba de gastar.
    "magi/core/kernel.py": 1020,
    # +48 en la v5.5.2: el filtro de idioma que se le inyecta a Yqcloud por
    # API (responde en chino cuando le apetece) y el catálogo de la familia
    # `gpt` con WeWordle de vuelta, cada entrada con el motivo escrito.
    "magi/core/providers/backends/g4f_backend.py": 1050,
    "magi/core/sesion_web.py": 910,
    # +68 en la v5.5.2: presupuesto por tarea (contador, cierre por techo y
    # rehidratación), fan-out por motor y el candado que serializa el
    # despacho. Tres frenos que solo tienen sentido donde se decide gastar.
    # +95 más en la ejecución del megaplan: el contraste de la síntesis contra
    # el registro (C12) y el contrato de entregable (C4), que son las dos
    # piezas que impiden anunciar un .exe que no existe. Van aquí y no en un
    # módulo aparte porque las dos leen el `state` de la tarea, que es de esta
    # clase: sacarlas obligaría a exportar el estado entero, que es peor.
    "magi/modules/swarm/orchestrator.py": 1160,
}

#: Para todo lo demás. 800 líneas es mucho para un módulo de Python, y ninguno
#: de los que no están arriba se acerca: el techo general no molesta a nadie
#: hoy y frena al primero que se desmadre mañana.
TECHO_GENERAL = 800


def _modulos() -> list[pathlib.Path]:
    return sorted(p for p in (RAIZ / "magi").rglob("*.py")
                  if "_attic" not in p.parts and "__pycache__" not in p.parts)


@pytest.mark.parametrize("ruta", _modulos(),
                         ids=lambda p: str(p.relative_to(RAIZ)).replace("\\", "/"))
def test_ningun_modulo_crece_por_encima_de_su_techo(ruta: pathlib.Path):
    rel = str(ruta.relative_to(RAIZ)).replace("\\", "/")
    lineas = len(ruta.read_text(encoding="utf-8").splitlines())
    techo = TECHOS.get(rel, TECHO_GENERAL)

    assert lineas <= techo, (
        f"{rel}: {lineas} líneas, techo {techo}.\n"
        f"\n"
        f"No es una regla de estilo. Un fichero de mil líneas es un fichero "
        f"que nadie relee entero, y ahí es donde se esconden los bucles que "
        f"no terminan y los `if` que no comprueban nada.\n"
        f"\n"
        f"Dos salidas honestas:\n"
        f"  1) Extrae una pieza a su propio módulo (lo normal).\n"
        f"  2) Sube el techo AQUÍ y explica en el commit por qué este fichero "
        f"tiene que ser más grande. Lo que no vale es crecer sin que nadie "
        f"lo decida.")


def test_los_techos_apuntan_a_ficheros_que_existen():
    """
    Un techo para un fichero borrado o renombrado no protege nada y da la
    sensación de que sí. Es el mismo fallo que una marca de pytest que no
    existe: parece una garantía y no lo es.
    """
    faltan = [rel for rel in TECHOS if not (RAIZ / rel).is_file()]
    assert not faltan, f"techos huérfanos, bórralos o corrígelos: {faltan}"


def test_ningun_techo_esta_muy_por_encima_de_la_realidad():
    """
    EL TRINQUETE TIENE QUE APRETAR.

    Si un fichero adelgaza y su techo se queda arriba, deja de frenar nada: se
    puede volver a engordar hasta el número viejo sin que nada avise. Este test
    obliga a bajar el techo cuando el fichero baja, que es la mitad del
    mecanismo — la que se olvida siempre.
    """
    flojos = []
    for rel, techo in TECHOS.items():
        lineas = len((RAIZ / rel).read_text(encoding="utf-8").splitlines())
        if techo - lineas > HOLGURA * 3:
            flojos.append(f"{rel}: {lineas} líneas con techo {techo}")
    assert not flojos, (
        "estos techos han quedado holgados; bájalos a lo medido + "
        f"{HOLGURA} para que vuelvan a frenar:\n  " + "\n  ".join(flojos))
