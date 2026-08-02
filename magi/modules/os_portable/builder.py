class OsBuilder:
    """
    Constructor Reproducible (P16.b).
    Garantiza hashes idénticos a partir de la misma receta YAML.
    """
    def build_image(self, recipe: dict) -> dict:
        """
        Simula la compilación de Buildroot/Alpine.
        """
        # Determinar reproducibilidad
        if recipe.get("reproducible", {}).get("source_date_epoch") is not None:
             # Hash estable simulado
             img_hash = f"sha256:repro_img_{recipe['name']}"
             return {"image_path": "/tmp/img.qcow2", "hash": img_hash, "manifest": recipe.get("manifest", [])}
             
        return {"image_path": "/tmp/img_unstable.qcow2", "hash": "sha256:random_84930", "manifest": recipe.get("manifest", [])}
