"""Normalizacion linguistica del texto, a mano (sin librerias de NLP).

Pipeline: minusculas -> quitar puntuacion -> tokenizar -> quitar stopwords -> stemming.
El MISMO tokenizer se usa al construir el indice y al procesar la consulta, para
que los terminos sean comparables.
"""

from __future__ import annotations


class Tokenizer:
    def __init__(self, language: str = "spanish", use_stemming: bool = True):
        """
        stopwords: cargadas desde un archivo local (no librerias).
        use_stemming: aplica un stemmer propio (p. ej. reglas tipo Porter ligero).
        """
        self.language = language
        self.use_stemming = use_stemming
        self.stopwords: set[str] = set()  # cargar en _load_stopwords()

    def normalize(self, text: str) -> str:
        """Pasa a minusculas y elimina puntuacion/acentos. Salida: texto limpio."""
        raise NotImplementedError

    def tokenize(self, text: str) -> list[str]:
        """Divide el texto normalizado en tokens. Salida: lista de tokens crudos."""
        raise NotImplementedError

    def remove_stopwords(self, tokens: list[str]) -> list[str]:
        """Filtra palabras vacias usando self.stopwords."""
        raise NotImplementedError

    def stem(self, token: str) -> str:
        """Reduce un token a su raiz con reglas propias (sin librerias)."""
        raise NotImplementedError

    def process(self, text: str) -> list[str]:
        """Pipeline completo: normalize -> tokenize -> remove_stopwords -> stem.

        Salida: lista final de terminos lista para contar frecuencias (TF).
        """
        raise NotImplementedError

    def _load_stopwords(self, path: str) -> set[str]:
        raise NotImplementedError
