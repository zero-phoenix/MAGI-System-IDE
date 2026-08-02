import os
import json
import logging
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class AASLoader:
    """
    Cargador del catálogo de agentic-awesome-skills.
    Escanea el directorio de skills clonado e indexa sus metadatos básicos
    para hacerlos disponibles al Enjambre a través de la pizarra (Blackboard).
    """
    def __init__(self, repo_path: str = "d:/PROYECTOS/MAGI System IDE/scratch/agentic-awesome-skills"):
        self.repo_path = Path(repo_path)
        self.skills = {}
        self.skill_ids = []
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = None
        
    def load(self):
        """Descubre e indexa los skills disponibles."""
        if not self.repo_path.exists():
            logger.warning(f"[AASLoader] Repositorio {self.repo_path} no encontrado.")
            return 0
            
        plugins_dir = self.repo_path / "plugins"
        if not plugins_dir.exists():
            logger.warning("[AASLoader] Directorio 'plugins' no encontrado.")
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
                    except:
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
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
                
        logger.info(f"[AASLoader] {count} skills de agentic-awesome-skills indexadas y vectorizadas (TF-IDF) exitosamente.")
        return count

    def search(self, query: str, top_k: int = 5):
        """Busca las skills más relevantes usando RAG (TF-IDF y Similitud del Coseno)."""
        if not self.skills or self.tfidf_matrix is None:
            return "No hay skills disponibles."
            
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
