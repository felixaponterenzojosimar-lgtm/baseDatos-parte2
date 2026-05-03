from enum import Enum, auto
from threading import Lock


class LockMode(Enum):
    SHARED = "S"
    EXCLUSIVE = "X"


# Compatibility: can new_mode be granted if current_mode is held?
_COMPATIBLE = {
    LockMode.SHARED:    {LockMode.SHARED: True,  LockMode.EXCLUSIVE: False},
    LockMode.EXCLUSIVE: {LockMode.SHARED: False, LockMode.EXCLUSIVE: False},
}


class LockManager:
    """
    Gestiona bloqueos compartidos/exclusivos por ítem.
    Shared (S): múltiples lectores simultáneos.
    Exclusive (X): escritura exclusiva.
    """

    def __init__(self):
        self._mutex = Lock()
        # item -> {"mode": LockMode, "holders": set[tx_id]}
        self._locks: dict[str, dict] = {}
        # tx_id -> {item, mode} — operación bloqueada esperando
        self._waiting: dict[int, dict] = {}

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def acquire(self, tx_id: int, item: str, mode: LockMode) -> bool:
        """
        Intenta adquirir un bloqueo.
        Returns True si se otorgó, False si debe esperar.
        """
        with self._mutex:
            lock = self._locks.get(item)

            if lock is None:
                self._locks[item] = {"mode": mode, "holders": {tx_id}}
                return True

            holders = lock["holders"]
            current_mode = lock["mode"]

            # Ya tiene el lock
            if tx_id in holders:
                # Upgrade S → X
                if mode == LockMode.EXCLUSIVE and current_mode == LockMode.SHARED:
                    if len(holders) == 1:
                        lock["mode"] = LockMode.EXCLUSIVE
                        return True
                    # Otros también tienen S, no se puede upgradear ahora
                    self._waiting[tx_id] = {"item": item, "mode": mode}
                    return False
                return True

            # Verificar compatibilidad
            if _COMPATIBLE[current_mode][mode] and _COMPATIBLE[mode][current_mode]:
                # S + S: compatibles
                holders.add(tx_id)
                return True

            # Incompatible — debe esperar
            self._waiting[tx_id] = {"item": item, "mode": mode}
            return False

    def release(self, tx_id: int, item: str) -> None:
        with self._mutex:
            lock = self._locks.get(item)
            if lock is None:
                return
            lock["holders"].discard(tx_id)
            if not lock["holders"]:
                del self._locks[item]

    def release_all(self, tx_id: int) -> None:
        with self._mutex:
            to_remove = [item for item, lock in self._locks.items()
                         if tx_id in lock["holders"]]
            for item in to_remove:
                lock = self._locks[item]
                lock["holders"].discard(tx_id)
                if not lock["holders"]:
                    del self._locks[item]
            self._waiting.pop(tx_id, None)

    def detect_deadlock(self) -> list[int]:
        """
        Construye el grafo de espera y detecta ciclos.
        Returns lista de tx_ids en el ciclo, o [] si no hay deadlock.
        """
        with self._mutex:
            # wait_for[tx] = set de tx que lo bloquean
            wait_for: dict[int, set] = {}
            for waiter, info in self._waiting.items():
                item = info["item"]
                lock = self._locks.get(item)
                if lock:
                    blockers = lock["holders"] - {waiter}
                    if blockers:
                        wait_for[waiter] = blockers

        return self._find_cycle(wait_for)

    def lock_table_snapshot(self) -> dict:
        """Retorna estado actual de la tabla de locks (sin mutex — solo para reporte)."""
        return {
            item: {"mode": lock["mode"].value, "holders": sorted(lock["holders"])}
            for item, lock in self._locks.items()
        }

    def waiting_snapshot(self) -> dict:
        return {
            tx_id: {"item": info["item"], "mode": info["mode"].value}
            for tx_id, info in self._waiting.items()
        }

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------

    def _find_cycle(self, graph: dict[int, set]) -> list[int]:
        visited: set = set()
        path: list = []

        def dfs(node):
            if node in path:
                return path[path.index(node):]
            if node in visited:
                return []
            visited.add(node)
            path.append(node)
            for neighbor in graph.get(node, set()):
                cycle = dfs(neighbor)
                if cycle:
                    return cycle
            path.pop()
            return []

        for node in list(graph.keys()):
            if node not in visited:
                cycle = dfs(node)
                if cycle:
                    return cycle
        return []
