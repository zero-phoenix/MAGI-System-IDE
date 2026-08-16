import hashlib
import logging
from pathlib import Path
from typing import Any

import jinja2

logger = logging.getLogger(__name__)

class PromptCompiler:
    """
    Ensamblador de plantillas Jinja2 para el Área 7.
    Compone base + rol + dominio en un solo texto y calcula su SHA-256 (prompt_hash).
    """
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(templates_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )

    def compile(self, role: str, domain: str, ctx: dict[str, Any], capabilities: list[str] = None) -> tuple[str, str]:
        """
        Renderiza el prompt combinando base, rol, dominio y capacidades.
        Devuelve (prompt_renderizado, prompt_hash).
        """
        try:
            capabilities = capabilities or []
            # 1. Cargar plantillas
            base_template = self.env.get_template("base/forensic_engineer.md.j2")
            role_template = self.env.get_template(f"roles/{role}.md.j2")

            domain_template_name = f"domains/{domain}.md.j2"
            try:
                domain_template = self.env.get_template(domain_template_name)
            except jinja2.exceptions.TemplateNotFound:
                logger.warning(f"Domain template '{domain}' not found. Skipping domain instructions.")
                domain_template = None

            # 2. Renderizar bloques
            base_rendered = base_template.render(**ctx)
            role_rendered = role_template.render(**ctx)
            domain_rendered = domain_template.render(**ctx) if domain_template else ""

            cap_rendered = []
            for cap in capabilities:
                try:
                    ctemp = self.env.get_template(f"capabilities/{cap.lower()}.md.j2")
                    cap_rendered.append(ctemp.render(**ctx))
                except jinja2.exceptions.TemplateNotFound:
                    logger.warning(f"Capability template '{cap}' not found. Skipping.")

            # 3. Ensamblar prompt completo
            parts = [base_rendered.strip(), role_rendered.strip()]
            if domain_rendered:
                parts.append(domain_rendered.strip())
            if cap_rendered:
                parts.append("CAPACIDADES INYECTADAS:\n" + "\n\n".join(c.strip() for c in cap_rendered))

            prompt_text = "\n\n---\n\n".join(parts)

            # 4. Calcular SHA-256 (prompt_hash)
            # Debe calcularse sobre el render final para invalidar cachés si algo cambia
            prompt_hash = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()

            return prompt_text, prompt_hash

        except Exception as e:
            logger.error(f"Error compilando prompt (role={role}, domain={domain}): {e}")
            raise
