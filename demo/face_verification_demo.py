"""
DEMO ONLY – NOT FOR PRODUCTION

Demo face verification simulation.

This module provides SIMULATED face verification for demonstration purposes only.
It does NOT use real images, real embeddings, or real biometric processing.

Purpose:
- Explain face verification concepts during project reviews
- Demonstrate how embedding similarity works conceptually
- NOT to claim accuracy or real face recognition

IMPORTANT:
- No real images are used
- Embeddings are completely simulated
- No real biometric processing occurs
- Results are for demonstration only
"""

import random
import numpy as np
from typing import Literal, Tuple
from app.config import DEMO_MODE


def generate_fake_embedding(seed: int = None) -> np.ndarray:
    """
    DEMO ONLY – NOT FOR PRODUCTION
    
    Generates a fake/simulated face embedding vector.
    
    This function creates a random normalized vector that simulates what
    a real face embedding would look like. The embedding is NOT from any
    real image or face recognition model.
    
    Args:
        seed: Optional random seed for reproducibility
        
    Returns:
        Normalized embedding vector (128-dimensional, unit length)
        
    IMPORTANT:
    - This is NOT a real embedding from any face image
    - The vector is randomly generated for demonstration
    - No real biometric data is used
    """
    if not DEMO_MODE:
        raise RuntimeError(
            "DEMO ONLY: This function requires DEMO_MODE=True. "
            "This is not for production use."
        )
    
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    # Generate random vector (128 dimensions, typical for face embeddings)
    embedding_dim = 128
    embedding = np.random.randn(embedding_dim).astype(np.float32)
    
    # Normalize to unit length (standard for face embeddings)
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    
    return embedding


def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    DEMO ONLY – NOT FOR PRODUCTION
    
    Computes cosine similarity between two embedding vectors.
    
    For normalized embeddings (unit length), cosine similarity simplifies
    to the dot product:
    similarity = dot(emb1, emb2) / (||emb1|| × ||emb2||) = dot(emb1, emb2)
    
    Args:
        embedding1: First embedding vector (normalized)
        embedding2: Second embedding vector (normalized)
        
    Returns:
        Cosine similarity score in range [-1, 1], typically [0, 1] for normalized embeddings
        
    IMPORTANT:
    - This function works with simulated embeddings only
    - No real face recognition is performed
    """
    if not DEMO_MODE:
        raise RuntimeError(
            "DEMO ONLY: This function requires DEMO_MODE=True. "
            "This is not for production use."
        )
    
    # Ensure numpy arrays
    if isinstance(embedding1, list):
        embedding1 = np.array(embedding1)
    if isinstance(embedding2, list):
        embedding2 = np.array(embedding2)
    
    # Compute dot product (for normalized vectors, this is cosine similarity)
    dot_product = np.dot(embedding1, embedding2)
    
    # Clamp to valid range (should be [-1, 1] for normalized vectors)
    similarity = float(np.clip(dot_product, -1.0, 1.0))
    
    return similarity


def verify_demo_face(
    user_type: Literal["same_person", "different_person"]
) -> Tuple[float, str]:
    """
    DEMO ONLY – NOT FOR PRODUCTION
    
    Simulates face verification by generating fake embeddings and comparing them.
    
    This function:
    1. Generates two fake embeddings
    2. For "same_person": generates similar embeddings (high similarity)
    3. For "different_person": generates different embeddings (low similarity)
    4. Computes cosine similarity
    5. Returns match result based on threshold
    
    Args:
        user_type: "same_person" or "different_person" to simulate the scenario
        
    Returns:
        Tuple of (similarity_score, result):
        - similarity_score: Float between 0.0 and 1.0
        - result: "MATCH" or "NO_MATCH"
        
    IMPORTANT:
    - No real images are used
    - Embeddings are completely simulated
    - No real biometric processing occurs
    - Results are for demonstration purposes only
    """
    if not DEMO_MODE:
        raise RuntimeError(
            "DEMO ONLY: This function requires DEMO_MODE=True. "
            "This is not for production use."
        )
    
    # Verification threshold (standard for face verification)
    threshold = 0.8
    
    if user_type == "same_person":
        # Generate two similar embeddings for same person
        # Use same seed with slight variation to ensure high similarity
        base_seed = random.randint(0, 10000)
        embedding1 = generate_fake_embedding(seed=base_seed)
        
        # Create similar embedding by adding small random noise
        noise = np.random.randn(128).astype(np.float32) * 0.1  # Small noise
        embedding2 = embedding1 + noise
        # Renormalize
        norm = np.linalg.norm(embedding2)
        if norm > 0:
            embedding2 = embedding2 / norm
        
        # Compute similarity (should be high for same person)
        similarity = cosine_similarity(embedding1, embedding2)
        
        # Ensure similarity is above threshold for same person
        # Add some randomness but keep it high
        if similarity < threshold:
            similarity = threshold + random.uniform(0.0, 0.15)
            similarity = min(similarity, 1.0)
    
    else:  # different_person
        # Generate two different embeddings for different person
        embedding1 = generate_fake_embedding(seed=random.randint(0, 10000))
        embedding2 = generate_fake_embedding(seed=random.randint(0, 10000))
        
        # Compute similarity (should be low for different person)
        similarity = cosine_similarity(embedding1, embedding2)
        
        # Ensure similarity is below threshold for different person
        # Add some randomness but keep it low
        if similarity >= threshold:
            similarity = threshold - random.uniform(0.1, 0.3)
            similarity = max(similarity, 0.0)
    
    # Determine result based on threshold
    if similarity >= threshold:
        result = "MATCH"
    else:
        result = "NO_MATCH"
    
    return similarity, result

