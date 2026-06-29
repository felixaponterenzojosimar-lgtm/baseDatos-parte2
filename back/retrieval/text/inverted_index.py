"""Indice invertido de texto persistido en disco (memoria secundaria).

Archivos (escritos por SpimiBuilder):
  - postings.jsonl   : una linea por termino -> {"t": term, "p": [[doc_id, tf], ...]}
  - dictionary.json  : term -> {df, idf, offset}  (offset = byte donde empieza su linea)
  - norms.json       : doc_id -> norma TF-IDF (para normalizar el coseno)
  - meta.json        : {num_docs}

La consulta NO carga los postings completos: usa el diccionario (liviano) para
hacer seek al offset del termino y leer solo su linea.
"""

from __future__ import annotations

import json
from pathlib import Path


class InvertedIndex:
    def __init__(self, index_dir: str):
        self.index_dir = Path(index_dir)
        self.postings_path = self.index_dir / "postings.jsonl"
        self.dictionary: dict[str, dict] = {}
        self.norms: dict[int, float] = {}
        self.num_docs: int = 0
        self._postings_file = None  # handle abierto para seek

    def load(self) -> None:
        """Carga a RAM solo lo liviano (diccionario + normas + meta), no los postings."""
        self.dictionary = json.loads((self.index_dir / "dictionary.json").read_text(encoding="utf-8"))
        raw_norms = json.loads((self.index_dir / "norms.json").read_text(encoding="utf-8"))
        self.norms = {int(d): float(n) for d, n in raw_norms.items()}
        self.num_docs = json.loads((self.index_dir / "meta.json").read_text(encoding="utf-8"))["num_docs"]

    def _file(self):
        if self._postings_file is None:
            self._postings_file = self.postings_path.open("r", encoding="utf-8")
        return self._postings_file

    def get_postings(self, term: str) -> list[tuple[int, int]]:
        """Lee de disco los postings de un termino: [(doc_id, tf), ...].

        Hace seek al offset del termino (acceso directo, sin recorrer el archivo).
        """
        entry = self.dictionary.get(term)
        if entry is None:
            return []
        f = self._file()
        f.seek(entry["offset"])
        payload = json.loads(f.readline())
        return [(int(d), int(tf)) for d, tf in payload["p"]]

    def get_idf(self, term: str) -> float:
        entry = self.dictionary.get(term)
        return entry["idf"] if entry else 0.0

    def get_document_norm(self, doc_id: int) -> float:
        return self.norms.get(doc_id, 0.0)

    def index_size_bytes(self) -> int:
        total = 0
        for name in ("postings.jsonl", "dictionary.json", "norms.json", "meta.json"):
            p = self.index_dir / name
            if p.is_file():
                total += p.stat().st_size
        return total

    def close(self) -> None:
        if self._postings_file is not None:
            self._postings_file.close()
            self._postings_file = None
