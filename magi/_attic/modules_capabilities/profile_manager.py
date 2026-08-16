import os


class ProfileManager:
    """
    Gestor de Perfiles Cognitivos (P12.a).
    Enlaza plantillas Jinja2 según el Capability ID y el rol (MELCHIOR, BALTHASAR, CASPER).
    """
    def __init__(self, templates_dir: str):
        self.templates_dir = templates_dir

    def render_prompt(self, capability_ids: list, node_role: str) -> str:
        """
        Simula la compilación del prompt inyectando los módulos solicitados.
        """
        prompt_parts = [f"System Role: {node_role}"]

        for cid in capability_ids:
            # Resolucion simple de nombres
            filename = ""
            if cid == "C01":
                filename = "c01_math.md.j2"
            elif cid == "C17":
                filename = "c17_logic.md.j2"

            if filename:
                filepath = os.path.join(self.templates_dir, filename)
                if os.path.exists(filepath):
                    with open(filepath, encoding="utf-8") as f:
                        prompt_parts.append(f.read().strip())
                else:
                    prompt_parts.append(f"{{Mocked Content for {cid}}}")

        return "\n\n".join(prompt_parts)
