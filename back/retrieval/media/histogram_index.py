"""KNN INDEXADO sobre histogramas mediante indice invertido de codewords.

Idea (analoga al indice invertido de texto): cada 'palabra visual/acustica' apunta
a los documentos cuyo histograma la contiene. En la consulta solo se evaluan los
documentos que comparten al menos una palabra con la consulta (candidatos), en vez
de toda la coleccion. Reduce el costo frente al KNN secuencial y mitiga en parte la
maldicion de la dimensionalidad al trabajar sobre histogramas dispersos.

Persistido en disco; construido al ejecutar CREATE INDEX ... USING MULTIMEDIA.
"""

from __future__ import annotations


class HistogramIndex:
    def __init__(self, index_dir: str):
        self.index_dir = index_dir
        self.postings: dict[int, list] = {}  # word_id -> [(doc_id, peso), ...]

    def build(self, sparse_histograms) -> None:
        """Construye el indice invertido de codewords y lo persiste.

        Entrada: iterable de (doc_id, {word_id: peso}).
        """
        raise NotImplementedError

    def knn(self, query_sparse: dict[int, float], k: int) -> list[tuple[int, float]]:
        """Top-k usando solo documentos candidatos (los que comparten codewords).

        Acumula similitud por documento recorriendo los postings de las palabras
        activas de la consulta; devuelve los k mejores con heap.
        """
        raise NotImplementedError

    def index_size_bytes(self) -> int:
        """Tamano en disco del indice (para la experimentacion)."""
        raise NotImplementedError
