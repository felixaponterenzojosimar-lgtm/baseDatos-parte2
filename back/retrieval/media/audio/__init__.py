"""Módulo específico para recuperación de audio.

Usa el pipeline compartido de media:
    audio_descriptor (MFCC) -> Vocabulary (K-Means) -> Histogram (BoAW)
    -> HistogramIndex / SequentialSearch -> KNN
"""

from ..media_retriever import MediaRetriever
from ..extractors.audio_descriptor import AudioDescriptorExtractor
from .preprocessor import AudioPreprocessor

__all__ = ["MediaRetriever", "AudioDescriptorExtractor", "AudioPreprocessor"]