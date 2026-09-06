"""
Las herramientas de LILIM, la capa local superveloz (megaplan v12).

Extraidas de builtin.py por el trinquete de líneas: son un dominio propio
(memoria local enciclopédica) y no mezclan con las herramientas de ficheros.
"""
from .builtin import ToolContext, ToolResult


def registrar(reg) -> None:
    @reg.tool("lilim_pregunta",
              "LILIM (capa local, sin red): responde al instante lo que MAGI "
              "ya sabe con procedencia — mandos de consolas y PC, "
              "decompilación/puertos estilo dusklight, repos del índice. Si "
              "no lo sabe, lo dice: no inventa.",
              {"type": "object", "properties": {
                  "pregunta": {"type": "string"}},
               "required": ["pregunta"]}, access={"read"})
    def lilim_pregunta(pregunta: str, ctx: ToolContext):
        from ...modules.lilim import pregunta as _preg
        return ToolResult(True, _preg(pregunta))

    @reg.tool("repos_de",
              "LILIM (local): los mejores repos de GitHub del índice curado "
              "para un tema (emudev, decomp, gamedev, vita, ia, tooling), con "
              "URL exacta. Metadatos, no clones.",
              {"type": "object", "properties": {
                  "tema": {"type": "string"}},
               "required": ["tema"]}, access={"read"})
    def repos_de(tema: str, ctx: ToolContext):
        from ...modules.lilim import repos_de as _repos
        return ToolResult(True, _repos(tema))

    @reg.tool("lilim_traduce",
              "LILIM (local): traduce la terminología técnica al instante "
              "entre es/en/de/ru/ja/zh desde la memoria, con procedencia. "
              "Frases completas que la memoria no cubre: el puente manda al "
              "enjambre de nube (se dice explícitamente).",
              {"type": "object", "properties": {
                  "texto": {"type": "string"},
                  "idioma": {"type": "string",
                             "description": "destino: es, en, de, ru, ja, zh"}},
               "required": ["texto", "idioma"]}, access={"read"})
    def lilim_traduce(texto: str, idioma: str, ctx: ToolContext):
        from ...modules.lilim import traduce as _traduce
        return ToolResult(True, _traduce(texto, idioma))

    @reg.tool("lilim_novedades",
              "LILIM (local): las novedades tecnológicas 2023-2026 en "
              "memoria (IA, baterías con IA en China, emulación, Python), "
              "cada una con su fuente para verificar. Lo no verificado se "
              "dice: SIN COMPROBAR.",
              {"type": "object", "properties": {
                  "tema": {"type": "string",
                           "description": "opcional: ia, baterias, "
                                          "hardware, emulacion, python"}},
               "required": []}, access={"read"})
    def lilim_novedades(tema: str = "", ctx: ToolContext = None):
        from ...modules.lilim import novedades as _nov
        return ToolResult(True, _nov(tema or ""))

    @reg.tool("lilim_ensenar",
              "LILIM (M4): guarda un conocimiento VERIFICADO con su URL de "
              "evidencia. Sin URL no entra — la enciclopedia sin procedencia "
              "es el sistema inventando más rápido. La próxima consulta "
              "sobre ese tema se responde local, en ms.",
              {"type": "object", "properties": {
                  "tema": {"type": "string"},
                  "afirmacion": {"type": "string"},
                  "url": {"type": "string"}},
               "required": ["tema", "afirmacion", "url"]}, access={"read"})
    def lilim_ensenar(tema: str, afirmacion: str, url: str, ctx: ToolContext):
        from ...modules.lilim import registrar_conocimiento as _reg
        ok = _reg(tema, afirmacion, url)
        return ToolResult(ok, "aprendido con procedencia" if ok else "",
                          error="" if ok else
                          "sin tema, afirmación o URL no hay conocimiento")
    @reg.tool("lilim_resuelve",
              "LILIM (motor EPD local): la consulta por el ciclo encode-"
              "prefill-decode sobre TODA la memoria, con su métrica MoE "
              "(qué dominios se activaron y qué % de la memoria). 0-4 ms, "
              "sin red, sin GPU. Lo desconocido: NO LO SÉ.",
              {"type": "object", "properties": {
                  "pregunta": {"type": "string"}},
               "required": ["pregunta"]}, access={"read"})
    def lilim_resuelve(pregunta: str, ctx: ToolContext):
        from ...modules.lilim.motor import motor
        r = motor.resolver(pregunta)
        return ToolResult(True, f"{r.activacion()} · {r.respuesta}")

    @reg.tool("lilim_multimodal",
              "LILIM (local, sin modelo): hechos DETERMINISTAS de un fichero "
              "o imagen — formato, dimensiones, peso, sha256. Lo que la "
              "imagen CONTIENE requiere visión: te dice a quién escalar.",
              {"type": "object", "properties": {
                  "ruta": {"type": "string"}},
               "required": ["ruta"]}, access={"read"})
    def lilim_multimodal(ruta: str, ctx: ToolContext):
        import json as _j

        from ...modules.lilim.rapida import hechos_de_imagen
        hechos = hechos_de_imagen(ruta)
        if "error" in hechos and "no existe" in hechos["error"]:
            return ToolResult(False, "", error=hechos["error"])
        return ToolResult(True, _j.dumps(hechos, ensure_ascii=False))

    @reg.tool("repos_clonar",
              "LILIM (L2): clon shallow (--depth 1) de un repositorio curado "
              "del índice repos_top.json al workspace, con registro en el "
              "journal para cumplir la compuerta A3 (código antes del build).",
              {"type": "object", "properties": {
                  "nombre": {"type": "string",
                             "description": "nombre en repos_top.json o URL git"},
                  "destino": {"type": "string",
                              "description": "directorio de destino en el workspace (opcional)"}},
               "required": ["nombre"]}, access={"write"})
    def repos_clonar(nombre: str, ctx: ToolContext, destino: str = ""):
        from ...modules.lilim import repos_clonar as _clonar
        dest_path = ctx.resolve(destino) if destino else None
        journal = ctx.get_journal() if hasattr(ctx, "get_journal") else None
        ok, msg, _ = _clonar(nombre, destino=dest_path, task_id=ctx.task_id, journal=journal)
        return ToolResult(ok, msg if ok else "", error="" if ok else msg)

    @reg.tool("repos_desregistrar",
              "LILIM (L2): des-registro limpio de un clon shallow en workspace, "
              "revirtiendo sus entradas en el journal.",
              {"type": "object", "properties": {
                  "destino": {"type": "string",
                              "description": "directorio a limpiar en el workspace"}},
               "required": ["destino"]}, access={"write"})
    def repos_desregistrar(destino: str, ctx: ToolContext):
        from ...modules.lilim import desregistrar_clon as _desreg
        dest_path = ctx.resolve(destino)
        journal = ctx.get_journal() if hasattr(ctx, "get_journal") else None
        ok, msg = _desreg(dest_path, task_id=ctx.task_id, journal=journal)
        return ToolResult(ok, msg if ok else "", error="" if ok else msg)



