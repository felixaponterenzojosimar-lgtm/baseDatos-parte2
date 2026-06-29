"""Wrapper específico para recuperación de audio.

Extiende MediaRetriever con funcionalidades específicas de audio:
- Preprocesamiento antes de extracción
- Métodos para búsqueda por similitud acústica
"""

from ..media_retriever import MediaRetriever
from .preprocessor import AudioPreprocessor


class AudioRetriever(MediaRetriever):
    def __init__(self, vocabulary, extractor, sequential, index, idf,
                 preprocessor: AudioPreprocessor = None):
        super().__init__(vocabulary, extractor, sequential, index, idf)
        self.preprocessor = preprocessor or AudioPreprocessor()

    def search(self, query_path: str, k: int, method: str | None = None) -> list[tuple[int, float]]:
        """Sobrescribe para incluir preprocesamiento si es necesario."""
        # El extractor ya maneja MFCC, pero podemos agregar preprocesamiento
        return super().search(query_path, k, method)