from .base_index import Index, DuplicateKeyError
from ..storage import Schema, PageManager, DiskStats


class SequentialFile(Index):
    """
    Archivo secuencial ordenado por clave primaria con archivo auxiliar
    de desbordamiento. Cuando el auxiliar alcanza K registros se hace
    una reconstrucción física del archivo principal.
    """

    K = 10  # umbral de registros en auxiliar antes de reconstruir

    def __init__(self, schema: Schema, page_manager: PageManager,
                 aux_page_manager: PageManager, stats: DiskStats):
        super().__init__(schema, page_manager, stats)
        self.aux_pm = aux_page_manager  # PageManager del archivo auxiliar

    def add(self, record: dict) -> None:
        """
        Input:  record  dict con todos los campos del schema
        Output: None
        — Escribe en el auxiliar.
        — Si auxiliar tiene K registros → reconstrucción.
        """
        pass

    def search(self, key) -> dict | None:
        """
        Input:  key  valor de la clave primaria
        Output: dict o None
        — Búsqueda binaria en principal + scan lineal en auxiliar.
        """
        pass

    def range_search(self, begin, end) -> list[dict]:
        """
        Input:  begin, end  valores de clave (inclusivos)
        Output: lista de registros
        — Binaria para begin, luego scan secuencial hasta end.
        """
        pass

    def remove(self, key) -> bool:
        """
        Input:  key  valor de la clave primaria
        Output: True/False
        — Marca con flag de eliminado. Se limpia en reconstrucción.
        """
        pass

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _rebuild(self) -> None:
        """Merge de principal + auxiliar → nuevo archivo principal ordenado."""
        pass

    def _binary_search(self, key) -> int:
        """Retorna page_id donde debería estar la clave en el archivo principal."""
        pass
