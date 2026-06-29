"""Descriptores locales de IMAGEN (SIFT).

Cada imagen produce un conjunto de descriptores locales (keypoints), analogos a
'palabras' antes de cuantizar contra el codebook visual.
"""

from __future__ import annotations


class ImageDescriptorExtractor:
    def __init__(self, max_keypoints: int = 500, resize_max_side: int = 512):
        """max_keypoints / resize: acotan costo y mitigan que imagenes grandes
        dominen el codebook (relacionado con la maldicion de la dimensionalidad)."""
        self.max_keypoints = max_keypoints
        self.resize_max_side = resize_max_side

    def extract(self, image_path: str):
        """Extrae descriptores SIFT.

        Salida: matriz (n_keypoints, 128) en float. Vacia si la imagen no tiene
        keypoints o no se puede leer. (Extraccion con OpenCV; el resto, a mano.)
        """
        raise NotImplementedError
