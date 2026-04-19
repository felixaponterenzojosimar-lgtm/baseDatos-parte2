from enum import Enum, auto
from dataclasses import dataclass, field
import time


class TxStatus(Enum):
    ACTIVE = auto()
    COMMITTED = auto()
    ABORTED = auto()


@dataclass
class LogEntry:
    tx_id: int
    operation: str   # "add" | "remove" | "search"
    table: str
    key: any
    timestamp: float = field(default_factory=time.time)


class Transaction:
    """
    Representa una transacción con su log de operaciones.
    """
    _counter = 0

    def __init__(self):
        Transaction._counter += 1
        self.tx_id = Transaction._counter
        self.status = TxStatus.ACTIVE
        self.log: list[LogEntry] = []

    def log_operation(self, operation: str, table: str, key: any) -> None:
        """
        Input:  operation  nombre de la operación
                table      nombre de la tabla
                key        clave involucrada
        Output: None — registra en self.log
        """
        pass

    def commit(self) -> None:
        """Output: None — cambia status a COMMITTED."""
        pass

    def abort(self) -> None:
        """Output: None — cambia status a ABORTED."""
        pass
