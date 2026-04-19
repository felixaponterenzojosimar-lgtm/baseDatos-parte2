import threading
from .transaction import Transaction
from .lock_manager import LockManager
from ..engine import Executor


class Scheduler:
    """
    Ejecuta múltiples transacciones de forma concurrente.
    Registra el orden de ejecución para identificar conflictos.
    """

    def __init__(self, executor: Executor, lock_manager: LockManager):
        self.executor = executor
        self.lock_manager = lock_manager
        self._active_txs: dict[int, Transaction] = {}
        self._log_lock = threading.Lock()
        self.global_log: list[dict] = []

    def begin_transaction(self) -> Transaction:
        """
        Output: Transaction nueva con status ACTIVE
        """
        pass

    def execute_in_transaction(self, tx: Transaction, sql: str) -> dict:
        """
        Input:  tx   Transaction activa
                sql  sentencia SQL a ejecutar dentro de la transacción
        Output: {"results": [...], "stats": {...}}
        — Adquiere bloqueos antes de ejecutar, libera al commit/abort.
        """
        pass

    def commit(self, tx: Transaction) -> None:
        """
        Input:  tx  Transaction a commitear
        Output: None — libera bloqueos y marca COMMITTED
        """
        pass

    def abort(self, tx: Transaction) -> None:
        """
        Input:  tx  Transaction a abortar
        Output: None — libera bloqueos y marca ABORTED
        """
        pass

    def run_concurrent(self, operations: list[tuple]) -> list[dict]:
        """
        Input:  operations  lista de (sql, tx_id) a ejecutar concurrentemente
        Output: lista de resultados en el orden en que se completaron
        — Lanza un thread por operación y registra el orden real de ejecución.
        """
        pass
