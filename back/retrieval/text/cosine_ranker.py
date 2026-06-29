"""Ranking por similitud de coseno TF-IDF sobre el indice invertido (a mano).

Algoritmo term-at-a-time:
  1. Vector TF-IDF disperso de la consulta.
  2. Por cada termino de la consulta, leer sus postings y acumular el producto
     punto en un acumulador {doc_id: score}.
  3. Normalizar por (norma_consulta * norma_documento) -> coseno.
  4. Top-k con heap (sin ordenar toda la coleccion).
"""

from __future__ import annotations

import heapq
import math
from collections import defaultdict

from .inverted_index import InvertedIndex


class CosineRanker:
    def __init__(self, index: InvertedIndex):
        self.index = index

    def query_vector(self, query_terms: list[str]) -> tuple[dict[str, float], float]:
        """Vector TF-IDF disperso de la consulta y su norma."""
        tf: dict[str, int] = defaultdict(int)
        for t in query_terms:
            tf[t] += 1
        vector: dict[str, float] = {}
        for term, freq in tf.items():
            idf = self.index.get_idf(term)
            if idf > 0:
                vector[term] = (1.0 + math.log(freq)) * idf
        norm = math.sqrt(sum(w * w for w in vector.values()))
        return vector, norm

    def rank(self, query_terms: list[str], k: int) -> list[tuple[int, float]]:
        """Top-k documentos por coseno usando el indice invertido."""
        if k <= 0:
            raise ValueError("k debe ser positivo")
        query, query_norm = self.query_vector(query_terms)
        if not query or query_norm == 0.0:
            return []

        scores: dict[int, float] = defaultdict(float)
        for term, q_weight in query.items():
            idf = self.index.get_idf(term)
            for doc_id, tf in self.index.get_postings(term):
                doc_weight = (1.0 + math.log(tf)) * idf
                scores[doc_id] += q_weight * doc_weight

        ranked: list[tuple[int, float]] = []
        for doc_id, dot in scores.items():
            denom = query_norm * self.index.get_document_norm(doc_id)
            ranked.append((doc_id, dot / denom if denom > 0 else 0.0))
        return heapq.nlargest(k, ranked, key=lambda item: (item[1], -item[0]))

    def rank_sequential(self, query_terms: list[str], k: int, documents) -> list[tuple[int, float]]:
        """Variante SECUENCIAL (sin indice): recorre todos los documentos y calcula
        coseno uno por uno. Baseline para la experimentacion (USING SEQUENTIAL).

        documents: iterable de (doc_id, terms:list[str]).
        """
        if k <= 0:
            raise ValueError("k debe ser positivo")
        query, query_norm = self.query_vector(query_terms)
        if not query or query_norm == 0.0:
            return []

        ranked: list[tuple[int, float]] = []
        for doc_id, terms in documents:
            tf: dict[str, int] = defaultdict(int)
            for t in terms:
                tf[t] += 1
            dot = 0.0
            norm_sq = 0.0
            for term, freq in tf.items():
                idf = self.index.get_idf(term)
                if idf <= 0:
                    continue
                weight = (1.0 + math.log(freq)) * idf
                norm_sq += weight * weight
                if term in query:
                    dot += query[term] * weight
            doc_norm = math.sqrt(norm_sq)
            score = dot / (query_norm * doc_norm) if doc_norm > 0 else 0.0
            ranked.append((doc_id, score))
        return heapq.nlargest(k, ranked, key=lambda item: (item[1], -item[0]))
