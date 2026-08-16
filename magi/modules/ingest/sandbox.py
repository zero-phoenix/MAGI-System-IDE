class SandboxWorker:
    """
    Simulador del entorno confinado (P15.f).
    Asegura que las herramientas peligrosas no toquen el sistema anfitrión.
    """
    def execute(self, tool_name: str, file_path: str) -> dict:
        """
        Ejecuta la herramienta de forma aislada.
        """
        # Simulación de fallos de herramientas
        if tool_name == "native_reader" and "WordPerfect" in file_path:
            return {"success": False, "reason": "No native reader found"}

        if tool_name == "specialized_lib" and "WordPerfect 1.0" in file_path:
            return {"success": False, "reason": "Library only supports v5.0+"}

        if tool_name == "salvage_strings":
            return {"success": True, "output": "Extracted RAW text strings"}

        return {"success": False, "reason": "Tool crashed"}
