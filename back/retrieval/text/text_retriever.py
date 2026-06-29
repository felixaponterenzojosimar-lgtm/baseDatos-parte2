"""Orquestador de la recuperacion textual (punto de entrada del operador @@).

Lo invoca executor._exec_text_search. Une tokenizer + inverted_index + cosine_ranker
y devuelve los (doc_id, score) top-k para que el executor resuelva las filas.
"""

from __future__ import annotations

from pathlib import Path

from .cosine_ranker import CosineRanker
from .inverted_index import InvertedIndex
from .spimi import SpimiBuilder
from .tokenizer import Tokenizer


class TextRetriever:
    def __init__(self, index: InvertedIndex, tokenizer: Tokenizer):
        self.index = index
        self.tokenizer = tokenizer
        self.ranker = CosineRanker(index)

    def search(self, query_text: str, k: int, method: str | None = None, documents=None) -> list[tuple[int, float]]:
        """Top-k (doc_id, score) por coseno.

        method:
            None | 'inverted'  -> ranking con el indice invertido (rapido)
            'sequential'       -> ranking por scan completo (requiere `documents`)
        """
        terms = self.tokenizer.process(query_text)
        if method == "sequential":
            if documents is None:
                raise ValueError("el modo secuencial requiere la coleccion `documents`")
            return self.ranker.rank_sequential(terms, k, documents)
        return self.ranker.rank(terms, k)

    @classmethod
    def build(cls, documents, index_dir: str, tokenizer: Tokenizer,
              block_size_postings: int = 100_000) -> "TextRetriever":
        """Construye el indice (via SpimiBuilder) y retorna un retriever listo.

        documents: iterable de (doc_id:int, raw_text:str). Se tokeniza cada uno con
        el mismo tokenizer antes de indexar. Lo usa CREATE INDEX ... USING INVERTED.
        """
        builder = SpimiBuilder(index_dir, block_size_postings=block_size_postings)
        tokenized = ((doc_id, tokenizer.process(text)) for doc_id, text in documents)
        index = builder.build(tokenized)
        return cls(index, tokenizer)

    @classmethod
    def open(cls, index_dir: str, tokenizer: Tokenizer) -> "TextRetriever":
        """Abre un indice ya construido en disco."""
        index = InvertedIndex(str(Path(index_dir)))
        index.load()
        return cls(index, tokenizer)
