"""Preprocesamiento de audio: eliminación de silencio, normalización, etc.

Operaciones opcionales antes de la extracción de MFCC para mejorar la calidad
de los descriptores.
"""

import numpy as np

class AudioPreprocessor:
    @staticmethod
    def remove_silence(signal, sr, threshold_db: float = -40, hop_length: int = 512):
        """Elimina segmentos de silencio del audio (opcional)."""
        # Implementación simple
        pass
    
    @staticmethod
    def normalize(signal):
        """Normaliza la amplitud del audio."""
        if signal.size == 0:
            return signal
        return signal / (np.max(np.abs(signal)) + 1e-10)
    
    @staticmethod
    def trim(signal, sr, max_duration: float = 30.0):
        """Recorta el audio a una duración máxima."""
        max_samples = int(sr * max_duration)
        if len(signal) > max_samples:
            return signal[:max_samples]
        return signal