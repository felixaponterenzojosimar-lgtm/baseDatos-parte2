import re
from .transaction import Transaction, TxStatus
from .lock_manager import LockManager, LockMode


class Scheduler:
    """
    Simulador de concurrencia con 2PL estricto.
    Toma un schedule como texto y retorna la traza paso a paso,
    con tabla de locks y detección de deadlocks.

    Formato de schedule:
        R1(A)  — T1 lee ítem A  (lock Shared)
        W2(B)  — T2 escribe ítem B  (lock Exclusive)
        C1     — T1 hace commit
        A2     — T2 aborta
    """

    _OP_RE = re.compile(r"^([RWrwCcAa])(\d+)(?:\(([^)]+)\))?$")

    def simulate(self, schedule_text: str) -> dict:
        ops = self._parse(schedule_text)
        transactions: dict[int, Transaction] = {}
        lm = LockManager()
        steps = []

        for raw, op_type, tid, item in ops:
            tx = transactions.setdefault(tid, Transaction(tid))

            if tx.status in (TxStatus.COMMITTED, TxStatus.ABORTED):
                steps.append(self._step(raw, tid, "skipped",
                                        f"T{tid} ya terminó — operación ignorada",
                                        lm))
                continue

            if op_type in ("R", "W"):
                mode = LockMode.SHARED if op_type == "R" else LockMode.EXCLUSIVE
                granted = lm.acquire(tid, item, mode)

                if granted:
                    tx.locks_held.add((item, mode))
                    tx.log_operation(op_type, item)
                    steps.append(self._step(raw, tid, "granted",
                                            f"T{tid} obtiene lock {mode.value} en {item}",
                                            lm))
                else:
                    tx.status = TxStatus.WAITING
                    steps.append(self._step(raw, tid, "blocked",
                                            f"T{tid} bloqueado esperando lock {mode.value} en {item} "
                                            f"(lo tiene: T{self._holder(lm, item, tid)})",
                                            lm))

                    # Detectar deadlock
                    cycle = lm.detect_deadlock()
                    if cycle:
                        victim = max(cycle)
                        victim_tx = transactions.get(victim)
                        if victim_tx:
                            lm.release_all(victim)
                            victim_tx.abort()
                        steps.append(self._step(
                            f"DEADLOCK",
                            victim,
                            "deadlock",
                            f"Deadlock detectado: ciclo {cycle} → T{victim} abortada (víctima = mayor tid)",
                            lm,
                        ))

            elif op_type == "C":
                lm.release_all(tid)
                tx.commit()
                steps.append(self._step(raw, tid, "committed",
                                        f"T{tid} commit — locks liberados",
                                        lm))

            elif op_type == "A":
                lm.release_all(tid)
                tx.abort()
                steps.append(self._step(raw, tid, "aborted",
                                        f"T{tid} abort — locks liberados",
                                        lm))

        summary = self._summary(transactions)
        return {"steps": steps, "summary": summary}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse(self, text: str) -> list[tuple]:
        ops = []
        for token in re.split(r"[\s,;]+", text.strip()):
            if not token:
                continue
            m = self._OP_RE.match(token)
            if not m:
                raise ValueError(f"Operación inválida: '{token}'. "
                                 "Formato: R1(A), W2(B), C1, A2")
            op_type = m.group(1).upper()
            tid = int(m.group(2))
            item = m.group(3)
            if op_type in ("R", "W") and not item:
                raise ValueError(f"'{token}': R y W requieren ítem, ej: R1(A)")
            ops.append((token, op_type, tid, item))
        return ops

    def _step(self, op: str, tid: int, result: str, message: str,
              lm: LockManager) -> dict:
        return {
            "op": op,
            "tid": tid,
            "result": result,
            "message": message,
            "lock_table": lm.lock_table_snapshot(),
            "waiting": lm.waiting_snapshot(),
        }

    def _holder(self, lm: LockManager, item: str, exclude_tid: int) -> str:
        lock = lm._locks.get(item)
        if not lock:
            return "?"
        others = lock["holders"] - {exclude_tid}
        return ", ".join(f"T{t}" for t in sorted(others)) or "?"

    def _summary(self, transactions: dict[int, Transaction]) -> dict:
        committed = [tid for tid, tx in transactions.items()
                     if tx.status == TxStatus.COMMITTED]
        aborted = [tid for tid, tx in transactions.items()
                   if tx.status == TxStatus.ABORTED]
        active = [tid for tid, tx in transactions.items()
                  if tx.status == TxStatus.ACTIVE]
        waiting = [tid for tid, tx in transactions.items()
                   if tx.status == TxStatus.WAITING]
        return {
            "committed": sorted(committed),
            "aborted": sorted(aborted),
            "active": sorted(active),
            "waiting": sorted(waiting),
        }
