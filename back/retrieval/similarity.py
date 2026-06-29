"""Funciones de similitud y distancia implementadas a mano (sin librerias).

Las usan tanto el ranker de texto (coseno sobre vectores TF-IDF dispersos) como
el KNN multimedia (distancia sobre histogramas densos de Bag of Words).
"""

from __future__ import annotations


def cosine_similarity_sparse(query: dict[int, float], document: dict[int, float]) -> float:
    """Similitud de coseno entre dos vectores dispersos {term_id: peso}.

    Entrada:
        query     vector disperso de la consulta (TF-IDF)
        document  vector disperso del documento (TF-IDF)
    Salida:
        coseno en [0, 1]; 0 si alguno es nulo.
    Nota:
        Se asume que los vectores YA estan normalizados o se normaliza aqui con
        las normas precalculadas del indice. Implementar recorriendo solo las
        claves en interseccion (eficiente para vectores dispersos).
    """
    raise NotImplementedError


def cosine_similarity_dense(a: list[float], b: list[float]) -> float:
    """Similitud de coseno entre dos vectores densos (histogramas)."""
    raise NotImplementedError


def euclidean_distance(a: list[float], b: list[float]) -> float:
    """Distancia euclidiana entre dos histogramas densos (para KNN)."""
    raise NotImplementedError


def l2_norm(vector) -> float:
    """Norma L2 de un vector (dict disperso o lista densa)."""
    raise NotImplementedError
