from typing import Dict, List, Any

class PortabilityMatrix:
    """
    Matriz de Arquitecturas y Clasificador de Capas (P5.3).
    Clasifica módulos en Agnósticos, Semi, o Específicos.
    """
    def __init__(self):
        pass
        
    def classify_layer(self, module_name: str, cpu_instructions: List[str]) -> str:
        """
        Si tiene instrucciones de CPU (ej. lw, sw) es Específico.
        Si sólo tiene algoritmia, es Agnóstico.
        """
        if any(instr in ["mfc0", "mtc0", "syscall", "lw", "sw"] for instr in cpu_instructions):
            return "specific"
        if len(cpu_instructions) == 0:
            return "agnostic"
        return "semi"
        
    def build_adaptation_ledger(self, src: str, target: str) -> Dict[str, Any]:
        """
        Libro Mayor de Adaptación.
        """
        return {
            "source_arch": src,
            "target_arch": target,
            "modules": {
                "core_fpu": "specific",
                "gui_menu": "agnostic"
            }
        }
