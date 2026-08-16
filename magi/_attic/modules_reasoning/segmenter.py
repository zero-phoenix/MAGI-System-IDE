import re


class LegalSegmenter:
    """
    Segmentador Jurídico (P2.a).
    Divide textos normativos en artículos localizables.
    """
    def __init__(self):
        # Regex para detectar "Artículo N", "Art. N", "Articulo N"
        self.article_pattern = re.compile(r'^(?:Artículo|Articulo|Art\.)\s+(\d+)', re.IGNORECASE | re.MULTILINE)

    def segment(self, text: str) -> list[dict[str, str]]:
        """
        Extrae los artículos y su texto, asignando un locator (ej. 'art_1').
        """
        matches = list(self.article_pattern.finditer(text))
        articles = []

        for i, match in enumerate(matches):
            art_num = match.group(1)
            start = match.start()
            end = matches[i+1].start() if i + 1 < len(matches) else len(text)

            content = text[start:end].strip()

            articles.append({
                "locator": f"art_{art_num}",
                "content": content
            })

        return articles
