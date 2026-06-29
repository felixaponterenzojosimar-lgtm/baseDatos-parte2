"""Ranking por similitud de coseno TF-IDF sobre el indice invertido.

Algoritmo (term-at-a-time, a mano):
  1. Construir el vector TF-IDF disperso de la consulta.
  2. Para cada termino de la consulta, leer sus postings del indice y acumular
     el producto punto en un acumulador {doc_id: score}.
  3. Normalizar cada score por (norma_consulta * norma_documento).
  4. Devolver los top-k con un heap (sin ordenar toda la coleccion).
"""

from __future__ import annotations

from .inverted_index import InvertedIndex


class CosineRanker:
    def __init__(self, index: InvertedIndex):
        self.index = index

    def query_vector(self, query_terms: list[str]) -> dict[str, float]:
        """Vector TF-IDF disperso de la consulta: termino -> peso."""
        raise NotImplementedError

    def rank(self, query_terms: list[str], k: int) -> list[tuple[int, float]]:
        """Top-k documentos por coseno.

        Entrada: terminos ya procesados por el tokenizer y k.
        Salida:  lista [(doc_id, score)] ordenada desc por score, longitud <= k.
        Usa acumulador por documento + heap para el top-k.
        """
        raise NotImplementedError

    def rank_sequential(self, query_terms: list[str], k: int, documents) -> list[tuple[int, float]]:
        """Variante SECUENCIAL (sin indice): recorre todos los documentos y calcula
        coseno uno por uno. Sirve de baseline en la experimentacion (USING SEQUENTIAL).
        """
        raise NotImplementedError
