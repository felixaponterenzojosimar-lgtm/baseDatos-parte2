"""Orquestador de la recuperacion textual (punto de entrada del operador @@).

Lo invoca executor._exec_text_search. Une tokenizer + inverted_index + cosine_ranker
y devuelve los identificadores (claves primarias) de los documentos top-k para que
el executor los resuelva contra la tabla.
"""

from __future__ import annotations

from .tokenizer import Tokenizer
from .inverted_index import InvertedIndex
from .cosine_ranker import CosineRanker


class TextRetriever:
    def __init__(self, index: InvertedIndex, tokenizer: Tokenizer):
        self.index = index
        self.tokenizer = tokenizer
        self.ranker = CosineRanker(index)

    def search(self, query_text: str, k: int, method: str | None = None) -> list[tuple[int, float]]:
        """Devuelve [(doc_id, score)] top-k.

        method:
            None | 'inverted'  -> ranking con el indice invertido (rapido)
            'sequential'       -> ranking por scan completo (baseline experimentos)
        """
        raise NotImplementedError

    @classmethod
    def build(cls, documents, index_dir: str, tokenizer: Tokenizer) -> "TextRetriever":
        """Construye el indice (via SpimiBuilder) y retorna un retriever listo.

        Lo usa el executor cuando se ejecuta CREATE INDEX ... USING INVERTED.
        """
        raise NotImplementedError
