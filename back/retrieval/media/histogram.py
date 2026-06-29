"""Histograma Bag of Visual/Acoustic Words, a mano.

Convierte la lista de word_id (salida de Vocabulary.quantize) en un histograma
normalizado de tamano k: cuantas veces aparece cada palabra en el item. Es el
'vector documento' que indexan y comparan los motores KNN.
"""

from __future__ import annotations


def build_histogram(word_ids: list[int], k: int, tf_idf: bool = True):
    """Construye el histograma de un item.

    Entrada: word_ids (palabras del item), k (tamano del codebook).
    Salida:  vector de longitud k. Si tf_idf, pondera por IDF y normaliza L2
             (mitiga el efecto de palabras muy frecuentes).
    """
    raise NotImplementedError


def compute_idf(histograms, k: int) -> list[float]:
    """IDF por palabra visual/acustica sobre toda la coleccion (para ponderar)."""
    raise NotImplementedError


def to_sparse(histogram) -> dict[int, float]:
    """Convierte un histograma denso a {word_id: peso} para el indice invertido."""
    raise NotImplementedError
