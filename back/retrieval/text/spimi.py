"""SPIMI: Single-Pass In-Memory Indexing (construccion en memoria secundaria).

Metodo optimizado para construir el indice invertido cuando la coleccion NO entra
en RAM (el enfoque que enseno el profesor, implementado a mano):

  1. Recorrer los documentos una sola vez acumulando postings en un diccionario
     en memoria hasta llenar un bloque (limite de memoria).
  2. Al llenarse, ordenar los terminos del bloque y volcarlo a disco como un
     bloque parcial ordenado.
  3. Repetir hasta procesar toda la coleccion -> varios bloques en disco.
  4. Merge multi-via (k-way) de los bloques ordenados -> un unico indice invertido
     final en disco (postings ordenados por termino).

No usa librerias: el orden, el volcado binario y el merge se hacen a mano.
"""

from __future__ import annotations


class SpimiBuilder:
    def __init__(self, output_dir: str, block_size_postings: int = 100_000):
        """
        output_dir: carpeta donde se escriben bloques parciales y el indice final.
        block_size_postings: cuantos postings caben en un bloque antes de volcar.
        """
        self.output_dir = output_dir
        self.block_size_postings = block_size_postings

    def build(self, documents) -> "InvertedIndex":  # noqa: F821
        """Construye el indice invertido completo desde la coleccion.

        Entrada:
            documents  iterable de (doc_id, terminos_procesados: list[str])
        Salida:
            InvertedIndex apuntando al indice final en disco.
        Pasos internos: _accumulate_block -> _flush_block (xN) -> _merge_blocks.
        """
        raise NotImplementedError

    def _flush_block(self, block: dict, block_number: int) -> str:
        """Ordena por termino y vuelca un bloque parcial a disco. Devuelve su ruta."""
        raise NotImplementedError

    def _merge_blocks(self, block_paths: list[str], final_path: str) -> None:
        """Merge k-way de bloques ordenados en el indice invertido final."""
        raise NotImplementedError

    def _compute_idf(self, document_frequencies: dict, num_docs: int) -> dict:
        """Calcula IDF por termino tras conocer la DF global (post-merge)."""
        raise NotImplementedError

    def _compute_document_norms(self) -> dict:
        """Calcula la norma TF-IDF de cada documento para normalizar el coseno."""
        raise NotImplementedError
