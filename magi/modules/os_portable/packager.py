class Packager:
    """
    Empaquetador y CTL-4 (P16.c, P16.e).
    Verifica las licencias antes de generar el ejecutable.
    """
    def package_single_executable(self, image_data: dict, target: str) -> dict:
        """
        Bloquea si hay software privado/propietario en el manifiesto.
        """
        manifest = image_data.get("manifest", [])
        
        for component in manifest:
            license = component.get("license", "").lower()
            if license in ["proprietary", "closed", "commercial"]:
                return {
                    "success": False,
                    "error": 'PackagingRefused(code="CTL4")',
                    "detail": f"Component {component['name']} has restricted license: {license}"
                }
                
        # Empaquetado exitoso
        return {"success": True, "artifact_path": f"/tmp/portable_vm_{target}.exe"}
