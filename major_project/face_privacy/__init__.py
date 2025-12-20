"""
Privacy-Preserving Face Verification Module

This module implements face verification using embeddings instead of raw images.
It provides privacy-preserving identity verification for the BrokeBuy marketplace.
"""

# Core components
from .verifier import (
    FaceVerifier,
    FaceEmbedding,
    VerificationResult,
    hash_image
)

__all__ = [
    "FaceVerifier",
    "FaceEmbedding",
    "VerificationResult",
    "hash_image",
]

