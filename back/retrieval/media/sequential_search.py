"""KNN SECUENCIAL sobre histogramas (baseline, fuerza bruta).

Recorre todos los histogramas de la coleccion, calcula la distancia/similitud con
el histograma consulta y mantiene los k mejores con un heap. Es el baseline contra
el cual se compara el KNN indexado (rubrica: 'secuencial e indexada').
"""

from __future__ import annotations


class SequentialSearch:
    def __init__(self, histograms_path: str, metric: str = "cosine"):
        """histograms_path: histogramas persistidos (uno por doc_id)."""
        self.histograms_path = histograms_path
        self.metric = metric

    def knn(self, query_histogram, k: int) -> list[tuple[int, float]]:
        """Top-k vecinos por fuerza bruta.

        Salida: [(doc_id, score)] ordenado, longitud <= k.
        Costo O(N): lee todos los histogramas. Usa heap para el top-k.
        """
        raise NotImplementedError
