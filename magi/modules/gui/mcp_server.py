class MCPServer:
    """
    Servidor Model Context Protocol (P10.d).
    Expone las herramientas del sistema al orquestador (ej: Claude Code).
    Asegura que operaciones R3 pasen a "pending_approval".
    """
    def __init__(self):
        self.tools = {
            "query_corpus": {"radius": "R0"},
            "flash_firmware": {"radius": "R3"},
            "slice_and_print": {"radius": "R3"}
        }

    def invoke_tool(self, tool_name: str, args: dict) -> dict:
        if tool_name not in self.tools:
            return {"error": "Tool not found"}

        radius = self.tools[tool_name]["radius"]

        if radius == "R3":
            # NUNCA ejecuta R3 directo. Pide aprobación (Área 8).
            return {
                "status": "pending_approval",
                "action_id": "act_999",
                "message": "Action requires human approval. Yielding."
            }

        if radius == "R0":
            return {"status": "success", "result": "Simulated R0 execution"}

        return {"error": "Unknown radius"}
