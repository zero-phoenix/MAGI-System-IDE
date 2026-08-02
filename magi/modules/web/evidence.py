import hashlib
from datetime import datetime

class EvidencePackager:
    """
    Empaquetador de Evidencia Web.
    Produce el paquete JSON inmutable que respalda las afirmaciones.
    """
    def create_package(self, page_data: dict, purpose: str) -> dict:
        content = page_data["a11y_snapshot"]
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        return {
            "evidence_id": f"wev_{hashlib.md5(content.encode('utf-8')).hexdigest()[:8]}",
            "url": page_data["url"],
            "fetched_at": datetime.now().isoformat(),
            "http_status": page_data["status"],
            "purpose": purpose,
            "a11y_snapshot_hash": content_hash,
            "engine": {
                "name": "camofox-browser",
                "fingerprint_profile": "estable-declarado"
            },
            "reproduce_cmd": f"magi web capture --url {page_data['url']} --profile estable-declarado"
        }
