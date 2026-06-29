"""Codebook (vocabulario de visual/acoustic words) via K-Means, a mano.

Agrupa TODOS los descriptores locales de la coleccion en k centroides. Cada
centroide es una 'palabra' (visual word / acoustic word). Cuantizar = asignar un
descriptor a su centroide mas cercano.

K-Means implementado a mano (init + asignacion + actualizacion + convergencia),
sin librerias de clustering. Para escalar se entrena sobre una muestra de descriptores.
"""

from __future__ import annotations


class Vocabulary:
    def __init__(self, k: int = 256, max_iter: int = 50, seed: int = 42):
        """k = numero de palabras del codebook (impacta precision vs costo/dimension)."""
        self.k = k
        self.max_iter = max_iter
        self.seed = seed
        self.centroids = None  # matriz (k, dim) tras fit()

    def fit(self, descriptors) -> None:
        """Entrena los k centroides con K-Means a mano sobre los descriptores dados."""
        raise NotImplementedError

    def quantize(self, descriptors) -> list[int]:
        """Asigna cada descriptor a su palabra mas cercana. Salida: lista de word_id."""
        raise NotImplementedError

    def save(self, path: str) -> None:
        """Persiste los centroides en disco (binario propio, sin librerias)."""
        raise NotImplementedError

    @classmethod
    def load(cls, path: str) -> "Vocabulary":
        raise NotImplementedError
