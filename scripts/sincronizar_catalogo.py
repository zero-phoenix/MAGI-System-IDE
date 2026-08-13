"""
Regenera `magi/data/catalogo_proveedores.json` DESDE las constantes de Python.

POR QUÉ EXISTE
==============
El mismo dato vive en dos sitios: `_FAMILY_SPECS_BASE` y compañía en
`g4f_backend.py` (el respaldo, para que el .exe arranque aunque el JSON falte o
esté corrupto) y el JSON empaquetado (editable sin recompilar 158 MB).

`test_el_json_dice_lo_mismo_que_las_constantes` comprueba que no diverjan, y
hace bien. Pero hasta hoy la única forma de mantenerlos iguales era editar los
dos a mano y confiar — y editar a mano dos copias del mismo dato es una
divergencia con fecha, no un riesgo.

Esto convierte la copia en derivación: las constantes de Python son la fuente,
el JSON se genera. Lo que el JSON añade —latencias medidas, fechas de
verificación, notas— se CONSERVA, porque el test no lo compara y porque es
justo lo que no cabe en una constante de Python.

USO
===
    python scripts/sincronizar_catalogo.py            # regenera
    python scripts/sincronizar_catalogo.py --revisar  # solo dice si divergen
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

DESTINO = RAIZ / "magi" / "data" / "catalogo_proveedores.json"


def construir() -> dict:
    from magi.core.providers.backends import g4f_backend as g

    previo = json.loads(DESTINO.read_text(encoding="utf-8"))
    fam_previas = previo.get("familias", {})

    # Índice de lo que el JSON sabe y las constantes no: latencia y fecha.
    medidas: dict[tuple[str, str, str | None], dict] = {}
    for fam, cuerpo in fam_previas.items():
        for c in cuerpo.get("candidatos", []):
            clave = (fam, c["proveedor"], c.get("modelo"))
            extra = {k: v for k, v in c.items()
                     if k not in ("proveedor", "modelo")}
            if extra:
                medidas[clave] = extra

    familias = {}
    for fam, cands in g._FAMILY_SPECS_BASE.items():
        lista = []
        for prov, mod in cands:
            entrada = {"proveedor": prov, "modelo": mod}
            entrada.update(medidas.get((fam, prov, mod), {}))
            lista.append(entrada)
        cuerpo = {"verificada": fam in g._VERIFICADAS_BASE, "candidatos": lista}
        nota = fam_previas.get(fam, {}).get("nota_orden")
        if nota:
            cuerpo["nota_orden"] = nota
        familias[fam] = cuerpo

    return {
        "schemaVersion": previo["schemaVersion"],
        "generado": previo["generado"],
        "nota": previo["nota"],
        "limites": previo["limites"],
        "hedge": {**previo.get("hedge", {}),
                  "tras_segundos": g._HEDGE_AFTER_S_BASE,
                  "maximo": g._HEDGE_MAX_BASE},
        "reparto_enjambre": dict(g._REPARTO_BASE),
        "reparto_enjambre_nota": previo.get("reparto_enjambre_nota", ""),
        "rotos": dict(g._ROTOS_BASE),
        "familias": familias,
    }


def main() -> int:
    nuevo = construir()
    texto = json.dumps(nuevo, ensure_ascii=False, indent=2) + "\n"
    if "--revisar" in sys.argv:
        igual = DESTINO.read_text(encoding="utf-8") == texto
        print("al dia" if igual else
              "DIVERGEN: ejecuta scripts/sincronizar_catalogo.py")
        return 0 if igual else 1
    DESTINO.write_text(texto, encoding="utf-8", newline="")
    print(f"{DESTINO.relative_to(RAIZ)} regenerado desde las constantes")
    print(f"  familias: {len(nuevo['familias'])}   rotos: {len(nuevo['rotos'])}")
    print(f"  reparto:  {nuevo['reparto_enjambre']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
