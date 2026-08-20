import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# numpy y sklearn se importan de forma DIFERIDA, y hay un matiz que decide si
# el diferimiento sirve de algo o es puro adorno.
#
# Antes estaban arriba, al nivel del módulo: el Kernel importa AASLoader, y eso
# arrastraba numpy + scipy + sklearn al arranque — unos 2,5 s de import en frío
# para algo que solo se usa al buscar skills. Bajarlos al __init__ NO arregla
# nada, porque kernel.py:42 hace `self.skills_loader = AASLoader()` en el
# constructor: el __init__ se ejecuta siempre y el import ocurre igual.
#
# El diferimiento real exige bajarlos hasta donde de verdad hacen falta: crear
# el vectorizador la primera vez que hay corpus que vectorizar. Con eso, la
# instalación típica —que no tiene clonado agentic-awesome-skills— no paga ni
# un milisegundo de sklearn, porque load() sale antes por el `exists()`.

class AASLoader:
    """
    Cargador del catálogo de agentic-awesome-skills.
    Escanea el directorio de skills clonado e indexa sus metadatos básicos
    para hacerlos disponibles al Enjambre a través de la pizarra (Blackboard).
    """
    def __init__(self, repo_path: str | None = None):
        from magi.core.paths import workspace_dir
        repo_path = repo_path or str(workspace_dir() / "agentic-awesome-skills")
        self.repo_path = Path(repo_path)
        self.skills = {}
        self.skill_ids = []
        # None hasta que haya algo que vectorizar. Ver _get_vectorizer().
        self.vectorizer = None
        self.tfidf_matrix = None

    def _get_vectorizer(self):
        """El vectorizador, creado la primera vez que se pide.

        Aquí es donde se paga el import de sklearn, y solo aquí: si no hay
        skills clonadas —el caso de casi cualquier instalación— no se paga
        nunca. El atributo sigue siendo `self.vectorizer`, así que quien lo
        leyera desde fuera ve lo mismo en cuanto hay índice.
        """
        if self.vectorizer is None:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vectorizer = TfidfVectorizer(stop_words='english')
        return self.vectorizer

    def load(self):
        """Descubre e indexa los skills disponibles."""
        # B10 — NO ES UN ERROR NO TENER UN REPOSITORIO OPCIONAL.
        #
        # Esto gritaba en WARNING en CADA arranque: «Repositorio ...
        # agentic-awesome-skills no encontrado». El catálogo de skills es
        # opcional y nadie lo clona, así que el aviso no describe un problema:
        # describe la instalación por defecto.
        #
        # Y el coste no es estético. Un log lleno de avisos que no significan
        # nada entrena a saltarse los avisos, y el día que salga uno de verdad
        # —el cortafuegos bloqueando un navegador, una invariante rota— pasará
        # desapercibido entre el ruido. Se degrada a debug, que es donde vive
        # lo que solo importa si lo vas buscando.
        if not self.repo_path.exists():
            logger.debug("[AASLoader] sin catálogo de skills en %s (opcional)",
                         self.repo_path)
            return 0

        plugins_dir = self.repo_path / "plugins"
        if not plugins_dir.exists():
            logger.debug("[AASLoader] el catálogo existe pero no tiene 'plugins'")
            return 0

        count = 0
        for skill_dir in plugins_dir.iterdir():
            if skill_dir.is_dir():
                skill_id = skill_dir.name
                # Leemos SKILL.md para embeddings precisos
                desc = f"Skill bundle: {skill_id.replace('-', ' ')}"
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    try:
                        desc = skill_md.read_text(encoding="utf-8")
                    except OSError:
                        pass

                self.skills[skill_id] = {
                    "id": skill_id,
                    "description": desc,
                    "path": str(skill_dir)
                }
                self.skill_ids.append(skill_id)
                count += 1

        if count > 0:
            corpus = [self.skills[sid]["description"] for sid in self.skill_ids]
            self.tfidf_matrix = self._get_vectorizer().fit_transform(corpus)

        logger.info(f"[AASLoader] {count} skills de agentic-awesome-skills indexadas y vectorizadas (TF-IDF) exitosamente.")
        return count

    def search(self, query: str, top_k: int = 5):
        """Busca las skills más relevantes usando RAG (TF-IDF y Similitud del Coseno)."""
        if not self.skills or self.tfidf_matrix is None or self.vectorizer is None:
            return "No hay skills disponibles."

        # Imports diferidos: numpy y sklearn solo hacen falta al buscar.
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity

        # Vectorizar la query y comparar
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Obtener los índices con mayor similitud
        top_indices = np.argsort(similarities)[::-1][:top_k]

        summary = "Skills recomendadas para esta tarea (RAG Vectorial):\\n"
        for idx in top_indices:
            score = similarities[idx]
            if score > 0.0:
                sid = self.skill_ids[idx]
                skill = self.skills[sid]
                summary += f"\\n- [Skill: {sid} | Ruta: {skill['path']} | Score de Relevancia: {score:.3f}]\\n"
                snippet = skill['description'][:150].replace('\\n', ' ')
                summary += f"  Descripción: {snippet}...\\n"

        if "Score de Relevancia" not in summary:
            for sid in self.skill_ids[:top_k]:
                summary += f"- {sid} (Ruta: {self.skills[sid]['path']})\\n"

        return summary
