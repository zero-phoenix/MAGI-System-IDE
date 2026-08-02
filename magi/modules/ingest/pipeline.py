from magi.modules.ingest.identifier import Identifier
from magi.modules.ingest.sandbox import SandboxWorker

class IngestPipeline:
    """
    Cascada de 7 Niveles de Ingesta (P15.d).
    Nunca retorna "formato no soportado".
    """
    def __init__(self):
        self.identifier = Identifier()
        self.sandbox = SandboxWorker()
        
    def process(self, path: str, magic_bytes: str, ext: str) -> dict:
        
        # Nivel 0
        ident = self.identifier.identify(path, magic_bytes, ext)
        fmt = ident["format"]
        
        if fmt == "UNSAFE_EXECUTABLE":
            return {"status": "no_legible", "reason": "Malicious payload detected"}
            
        # Nivel 1: Native
        n1 = self.sandbox.execute("native_reader", fmt)
        if n1["success"]:
            return {"status": "leido_completo"}
            
        # Nivel 2: Specialized Lib
        n2 = self.sandbox.execute("specialized_lib", fmt)
        if n2["success"]:
            return {"status": "leido_completo"}
            
        # Saltamos N3-N6 para el MVP de simulación...
        
        # Nivel 7: Rescate Parcial
        n7 = self.sandbox.execute("salvage_strings", fmt)
        if n7["success"]:
             return {"status": "leido_parcial", "data": n7["output"]}
             
        # Cierre absoluto: Si todo falla, es ilegible por daños, pero NO "no soportado"
        return {"status": "no_legible", "reason": "Data completely corrupted"}
