from .base_index import Index, DuplicateKeyError, NotSupportedError
from ..storage import Schema, PageManager, DiskStats


class ExtendibleHashing(Index):
    """
    Hashing extensible con directorio dinámico.
    No soporta range_search.
    Split de bucket cuando se desborda localmente.
    """

    BUCKET_SIZE = 4  # registros máximos por bucket antes de split

    def __init__(self, schema: Schema, page_manager: PageManager,
                 dir_page_manager: PageManager, stats: DiskStats):
        super().__init__(schema, page_manager, stats)
        self.dir_pm = dir_page_manager  # PageManager del directorio

    def add(self, record: dict) -> None:
        """
        Input:  record  dict con todos los campos del schema
        Output: None
        — hash(key) → bucket; si overflow → split.
        """
        pass

    def search(self, key) -> dict | None:
        """
        Input:  key  valor de la clave primaria
        Output: dict o None
        — hash(key) → leer página del bucket → buscar registro.
        """
        pass

    def range_search(self, begin, end) -> list[dict]:
        """No soportado en hashing extensible."""
        raise NotSupportedError("ExtendibleHashing no soporta range_search")

    def remove(self, key) -> bool:
        """
        Input:  key  valor de la clave primaria
        Output: True/False
        — hash(key) → bucket → eliminar entrada.
        """
        pass

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _hash(self, key, depth: int) -> int:
        """Retorna los `depth` bits menos significativos del hash de key."""
        pass

    def _split_bucket(self, bucket_index: int) -> None:
        """Divide el bucket y redistribuye sus registros."""
        pass

    def _read_directory(self) -> dict:
        """Lee el directorio desde disco. Retorna {prefijo_bits: page_id}."""
        pass

    def _write_directory(self, directory: dict) -> None:
        """Escribe el directorio en disco."""
        pass
