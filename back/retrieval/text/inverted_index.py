"""Indice invertido de texto persistido en disco (memoria secundaria).

Estructura en disco (escrita por SpimiBuilder, leida en consultas):
  - postings:  termino -> lista de (doc_id, tf)  [ordenado por termino]
  - vocabulario / diccionario:  termino -> (df, idf, offset_en_postings)
  - normas:    doc_id -> norma TF-IDF (para normalizar el coseno)

La consulta NO carga todo a RAM: usa el diccionario para hacer 'seek' al offset
del termino y leer solo su lista de postings.
"""

from __future__ import annotations


class InvertedIndex:
    def __init__(self, index_dir: str):
        """index_dir: carpeta con los archivos de postings, diccionario y normas."""
        self.index_dir = index_dir
        self.dictionary: dict[str, dict] = {}  # termino -> {df, idf, offset}
        self.num_docs: int = 0

    def load_dictionary(self) -> None:
        """Carga a RAM solo el diccionario liviano (terminos + offsets), no los postings."""
        raise NotImplementedError

    def get_postings(self, term: str) -> list[tuple[int, float]]:
        """Lee de disco la lista de postings de un termino: [(doc_id, tf), ...].

        Hace seek al offset del termino segun el diccionario (acceso por bloque).
        """
        raise NotImplementedError

    def get_idf(self, term: str) -> float:
        """IDF del termino (0 si no esta en el vocabulario)."""
        raise NotImplementedError

    def get_document_norm(self, doc_id: int) -> float:
        """Norma TF-IDF precalculada del documento (para el coseno)."""
        raise NotImplementedError

    def index_size_bytes(self) -> int:
        """Tamano total en disco del indice (para la experimentacion)."""
        raise NotImplementedError
