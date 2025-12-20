"""
Core Face Privacy Module

This package contains the core components for privacy-preserving face verification:
- Face embedding extraction and normalization
- Face verification using similarity metrics
- Privacy analysis and threat modeling
- Federated learning simulation (conceptual)
"""

from .embedding import FaceEmbedding, FaceEmbeddingExtractor
from .verify import FaceVerificationResult, verify_embeddings

__all__ = [
    "FaceEmbedding",
    "FaceEmbeddingExtractor",
    "FaceVerificationResult",
    "verify_embeddings",
]

