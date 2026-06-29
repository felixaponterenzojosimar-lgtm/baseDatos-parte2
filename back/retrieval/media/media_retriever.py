"""Orquestador de la recuperacion multimedia (punto de entrada del operador <->).

Lo invoca executor._exec_media_search. Une extractor + vocabulary + histogram con
el motor KNN (secuencial o indexado) y devuelve los doc_ids top-k.
"""

from __future__ import annotations

from .vocabulary import Vocabulary


class MediaRetriever:
    def __init__(self, vocabulary: Vocabulary, extractor, sequential, index):
        """
        vocabulary  : codebook entrenado (Vocabulary)
        extractor   : ImageDescriptorExtractor | AudioDescriptorExtractor
        sequential  : SequentialSearch (baseline)
        index       : HistogramIndex (KNN indexado)
        """
        self.vocabulary = vocabulary
        self.extractor = extractor
        self.sequential = sequential
        self.index = index

    def search(self, query_path: str, k: int, method: str | None = None) -> list[tuple[int, float]]:
        """Devuelve [(doc_id, score)] top-k.

        Pasos: extractor.extract -> vocabulary.quantize -> build_histogram ->
               KNN segun method:
                 None | 'multimedia' -> index.knn (indexado)
                 'sequential'        -> sequential.knn (baseline)
        """
        raise NotImplementedError

    @classmethod
    def build(cls, items, index_dir: str, extractor, k: int) -> "MediaRetriever":
        """Pipeline de construccion (CREATE INDEX ... USING MULTIMEDIA):
        extraer descriptores de todos los items -> entrenar Vocabulary ->
        construir histogramas -> persistir HistogramIndex -> retornar retriever.
        """
        raise NotImplementedError
