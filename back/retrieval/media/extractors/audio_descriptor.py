"""Descriptores locales de AUDIO (MFCC con ventana deslizante).

Cada audio produce una secuencia de vectores MFCC (uno por frame/ventana),
analogos a los keypoints SIFT: son las 'palabras' antes de cuantizar contra el
codebook acustico.
"""

from __future__ import annotations


class AudioDescriptorExtractor:
    def __init__(self, sample_rate: int = 22050, n_mfcc: int = 20,
                 window_ms: int = 100, hop_ms: int = 50):
        """Ventana deslizante de ~100-200 ms; cada ventana -> un vector MFCC."""
        self.sample_rate = sample_rate
        self.n_mfcc = n_mfcc
        self.window_ms = window_ms
        self.hop_ms = hop_ms

    def extract(self, audio_path: str):
        """Extrae descriptores MFCC.

        Salida: matriz (n_frames, n_mfcc) en float. Vacia si el audio no se puede
        leer. (Extraccion con librosa; el resto, a mano.)
        """
        raise NotImplementedError
