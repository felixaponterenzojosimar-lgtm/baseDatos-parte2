from abc import ABC, abstractmethod
from ..storage import Schema, PageManager, DiskStats


class Index(ABC):
    """
    Contrato que deben cumplir todos los índices.
    El Executor siempre llama a estos métodos sin importar la implementación.
    """

    def __init__(self, schema: Schema, page_manager: PageManager, stats: DiskStats):
        self.schema = schema
        self.pm = page_manager
        self.stats = stats

    @abstractmethod
    def add(self, record: dict) -> None:
        """
        Inserta un registro.
        Input:  record  dict con todos los campos del schema
        Output: None
        Raises: DuplicateKeyError si la clave ya existe
        """
        ...

    @abstractmethod
    def search(self, key) -> dict | None:
        """
        Búsqueda exacta por clave primaria.
        Input:  key     valor de la clave primaria (int, str, etc.)
        Output: dict con el registro, o None si no existe
        """
        ...

    @abstractmethod
    def range_search(self, begin, end) -> list[dict]:
        """
        Búsqueda por rango [begin, end] sobre la clave primaria.
        Input:  begin   valor mínimo (inclusivo)
                end     valor máximo (inclusivo)
        Output: lista de registros que cumplen begin <= key <= end
        Raises: NotSupportedError en ExtendibleHashing
        """
        ...

    @abstractmethod
    def remove(self, key) -> bool:
        """
        Elimina el registro con esa clave.
        Input:  key     valor de la clave primaria
        Output: True si se eliminó, False si no existía
        """
        ...


class DuplicateKeyError(Exception):
    pass


class NotSupportedError(Exception):
    pass
