from enum import Enum, auto
from threading import Lock


class LockMode(Enum):
    SHARED = auto()     # lectura
    EXCLUSIVE = auto()  # escritura


class LockManager:
    """
    Gestiona bloqueos a nivel de página (page_id).
    Shared: múltiples transacciones pueden leer simultáneamente.
    Exclusive: solo una transacción puede escribir.
    """

    def __init__(self):
        self._mutex = Lock()
        # {page_id: {"mode": LockMode, "holders": set[tx_id]}}
        self._locks: dict[int, dict] = {}

    def acquire(self, tx_id: int, page_id: int, mode: LockMode) -> bool:
        """
        Input:  tx_id    id de la transacción
                page_id  página que se quiere bloquear
                mode     SHARED o EXCLUSIVE
        Output: True si se adquirió el bloqueo, False si hay conflicto
        """
        pass

    def release(self, tx_id: int, page_id: int) -> None:
        """
        Input:  tx_id    id de la transacción
                page_id  página a liberar
        Output: None
        """
        pass

    def release_all(self, tx_id: int) -> None:
        """
        Input:  tx_id  libera todos los bloqueos de esta transacción
        Output: None
        """
        pass

    def detect_deadlock(self) -> list[int]:
        """
        Output: lista de tx_ids en deadlock (ciclo en el grafo de espera)
        """
        pass
