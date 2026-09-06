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
