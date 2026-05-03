from enum import Enum, auto
from dataclasses import dataclass, field
import time


class TxStatus(Enum):
    ACTIVE = auto()
    COMMITTED = auto()
    ABORTED = auto()
    WAITING = auto()


@dataclass
class LogEntry:
    tx_id: int
    operation: str   # "read" | "write" | "commit" | "abort"
    item: str
    timestamp: float = field(default_factory=time.time)


class Transaction:
    _counter = 0

    def __init__(self, tid: int = None):
        if tid is not None:
            self.tx_id = tid
        else:
            Transaction._counter += 1
            self.tx_id = Transaction._counter
        self.status = TxStatus.ACTIVE
        self.log: list[LogEntry] = []
        self.locks_held: set[tuple] = set()   # (item, LockMode)
        self.waiting_for: int | None = None   # tx_id it's blocked by

    def log_operation(self, operation: str, item: str) -> None:
        self.log.append(LogEntry(self.tx_id, operation, item))

    def commit(self) -> None:
        self.status = TxStatus.COMMITTED

    def abort(self) -> None:
        self.status = TxStatus.ABORTED
