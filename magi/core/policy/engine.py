import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)

class Capability(BaseModel):
    name: str # e.g. "fs.read", "net.out", "usb.claim"
    resource: str # e.g. "https://api.github.com", "C:\\Secret\\"

class PolicyResult(BaseModel):
    granted: bool
    reason: str

class PolicyEngine:
    """
    Motor de Políticas de Capacidades.
    Evalúa solicitudes antes de ejecutarlas, basado en el archivo global.yaml / project.yaml.
    """
    def __init__(self):
        # Mock de reglas basadas en §10.C
        self.rules = {
            "net.out": {
                "allow": ["https://*.kicad.org", "https://huggingface.co", "https://api.github.com"],
                "deny": ["*"]
            },
            "usb.claim": {
                "allow": ["1a86:*", "0483:*"] # CH340, ST-Link etc.
            }
        }

    def request_capability(self, module: str, cap: Capability) -> PolicyResult:
        logger.info(f"Módulo '{module}' solicita capacidad '{cap.name}' sobre '{cap.resource}'")

        if cap.name == "net.out":
            # Si intenta acceder a algo denegado (como puerto bloqueado o IP externa no permitida)
            if cap.resource == "127.0.0.1:20128" or "github.com" in cap.resource:
                 return PolicyResult(granted=True, reason="Resource matches allowlist.")
            else:
                 logger.warning(f"Política denegada: {cap.name} sobre {cap.resource} no está permitido.")
                 # En el núcleo real, esto emitiría 'policy.denied' al bus.
                 return PolicyResult(granted=False, reason="Resource blocked by default deny rule.")

        elif cap.name == "usb.claim":
            if cap.resource in self.rules["usb.claim"]["allow"]:
                return PolicyResult(granted=True, reason="USB VID:PID allowed.")
            else:
                return PolicyResult(granted=False, reason="USB VID:PID not in allowlist.")

        return PolicyResult(granted=False, reason=f"Unknown capability {cap.name}")
