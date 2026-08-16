import hashlib
from datetime import datetime


class EvidencePackager:
    """
    Empaquetador de Evidencia Web (A19-2).
    Produce el paquete JSON inmutable que respalda las afirmaciones.
    """
    def create_package(self, page_data: dict, purpose: str) -> dict:
        content = page_data["a11y_snapshot"]
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

        url = page_data["url"]

        # A19-2: Formato estricto para citar y verificar
        return {
            "evidence_id": f"wev_{hashlib.md5(content.encode('utf-8')).hexdigest()[:8]}",
            "url": url,
            "final_url": url,
            "fetched_at": datetime.now().isoformat(),
            "http_status": page_data["status"],
            "request_headers_ref": "cas://simulated-req-headers",
            "response_headers_ref": "cas://simulated-res-headers",
            "html_sha256": "simulated-html-hash",
            "a11y_snapshot_ref": f"cas://{content_hash}",
            "screenshot_ref": "cas://simulated-screenshot",
            "purpose": purpose,
            "robots_allowed": True,
            "session": None,
            "engine": {
                "name": "camofox-browser",
                "version": "1.0-mock",
                "fingerprint_profile": "estable-declarado"
            },
            "reproduce_cmd": f"magi web capture --url {url} --profile estable-declarado"
        }
