from .base_index import Index, DuplicateKeyError
from ..storage import Schema, PageManager, DiskStats


class BPlusTree(Index):
    """
    Árbol B+ con páginas de nodo de tamaño fijo (PAGE_SIZE).
    Las hojas están enlazadas para recorrido en range_search.
    """

    def __init__(self, schema: Schema, page_manager: PageManager, stats: DiskStats):
        super().__init__(schema, page_manager, stats)

    def add(self, record: dict) -> None:
        """
        Input:  record  dict con todos los campos del schema
        Output: None
        — Insertar en hoja; split si overflow; propagar hacia arriba.
        """
        pass

    def search(self, key) -> dict | None:
        """
        Input:  key  valor de la clave primaria
        Output: dict o None
        — Recorrer el árbol desde raíz hasta hoja.
        """
        pass

    def range_search(self, begin, end) -> list[dict]:
        """
        Input:  begin, end  valores de clave (inclusivos)
        Output: lista de registros
        — Llegar a la hoja de begin → recorrer hojas enlazadas hasta end.
        """
        pass

    def remove(self, key) -> bool:
        """
        Input:  key  valor de la clave primaria
        Output: True/False
        — Eliminar de hoja; merge o redistribuir si underflow.
        """
        pass

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _find_leaf(self, key) -> int:
        """Retorna el page_id de la hoja donde debería estar key."""
        pass

    def _split_leaf(self, page_id: int) -> tuple[int, any]:
        """Divide una hoja y retorna (nuevo_page_id, clave_promovida)."""
        pass

    def _split_internal(self, page_id: int) -> tuple[int, any]:
        """Divide un nodo interno y retorna (nuevo_page_id, clave_promovida)."""
        pass

    def _read_node(self, page_id: int) -> dict:
        """Deserializa una página → nodo {type, keys, children/records, next_leaf}."""
        pass

    def _write_node(self, page_id: int, node: dict) -> None:
        """Serializa un nodo → página y lo escribe en disco."""
        pass
