class MemgraphAdapter:
    """
    Adaptador de MAGI-MEM (P13.a).
    Se comunica con codebase-memory-mcp. En el MVP, simula la resolución de consultas.
    """
    def __init__(self):
        pass
        
    def search_graph(self, label: str = None, name_pattern: str = None) -> list:
        """
        Simula la búsqueda en el grafo AST.
        """
        if label == "Method" and name_pattern == "auth.*":
            return [
                {"id": "auth.login", "type": "Method", "file": "auth.py"},
                {"id": "auth.logout", "type": "Method", "file": "auth.py"}
            ]
        return []
        
    def trace_call_path(self, function_name: str, depth: int = 3) -> list:
        """
        Simula una traza de llamadas (Call Graph).
        """
        if function_name == "auth.login":
            return ["auth.login", "crypto.hash_password", "db.query_user"]
        return []
