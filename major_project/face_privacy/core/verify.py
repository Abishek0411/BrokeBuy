"""
Face Verification Logic

This module implements face verification using embedding similarity.
Verification determines if two face embeddings belong to the same person.

Why Cosine Similarity is Standard for Face Embeddings
------------------------------------------------------

1. **Normalized Embeddings**: Face embeddings are typically L2-normalized
   (unit length). For normalized vectors, cosine similarity simplifies to
   the dot product, making it computationally efficient.

2. **Scale Invariant**: Cosine similarity measures the angle between vectors,
   not their magnitude. This is ideal for face embeddings where the magnitude
   doesn't carry semantic meaning, only the direction (feature composition).

3. **Range**: Cosine similarity ranges from -1 to 1, but for normalized
   embeddings it's typically 0 to 1, where:
   - 1.0 = Identical faces (same person)
   - 0.8-0.99 = Very similar (likely same person)
   - < 0.7 = Different faces (different people)

4. **Well-Established**: Cosine similarity is the standard metric in face
   recognition research (FaceNet, ArcFace, etc.) and has been validated
   across many datasets.

5. **Interpretability**: The similarity score is intuitive - higher means
   more similar, making threshold selection understandable.

False Acceptance vs False Rejection Tradeoffs
----------------------------------------------

**False Acceptance (False Positive)**: System accepts an impostor as legitimate
- **Cost**: Security breach, account compromise
- **Impact**: High - fraudster gains access

**False Rejection (False Negative)**: System rejects a legitimate user
- **Cost**: User friction, support burden
- **Impact**: Medium - legitimate user inconvenienced

**Tradeoff**:
- **Strict Threshold (0.9)**: Low false acceptance, high false rejection
  - More secure, but many legitimate users rejected
  - Use case: High-security operations (account recovery, large transactions)
  
- **Moderate Threshold (0.8)**: Balanced
  - Good security/usability balance
  - Use case: Regular verification (login, transactions)
  
- **Lenient Threshold (0.7)**: High false acceptance, low false rejection
  - Less secure, but fewer legitimate users rejected
  - Use case: Low-risk operations (optional verification)

Why Conservative Thresholds Are Preferred in Student Systems
--------------------------------------------------------------

1. **Trust Building**: Student marketplaces need to build trust. Conservative
   thresholds (0.85+) ensure only verified users proceed, building platform
   credibility.

2. **Low False Positive Tolerance**: False acceptances (impostors) damage
   platform reputation more than false rejections (legitimate users can retry).

3. **Support Capacity**: Student-run systems have limited support capacity.
   Conservative thresholds reduce false rejections that require manual review.

4. **Legal Protection**: Conservative thresholds provide better legal protection
   if fraud occurs, showing due diligence in verification.

5. **Research Context**: This is a research prototype. Conservative thresholds
   demonstrate security-first approach, which is appropriate for academic work.
"""

from dataclasses import dataclass
from typing import Union, List
import numpy as np

from .embedding import FaceEmbedding


@dataclass
class FaceVerificationResult:
    """
    Result of a face verification operation.
    
    Attributes:
        is_match: Whether the two faces match (same person)
        similarity_score: Similarity score between embeddings (0-1)
        threshold_used: Threshold used for decision
        confidence: Confidence in the decision (distance from threshold)
        model_name: Embedding model used
    """
    is_match: bool
    similarity_score: float
    threshold_used: float
    confidence: float
    model_name: str
    
    def __str__(self) -> str:
        """String representation of verification result."""
        status = "MATCH" if self.is_match else "NO MATCH"
        return (f"Verification: {status} | "
                f"Similarity: {self.similarity_score:.4f} | "
                f"Threshold: {self.threshold_used:.4f} | "
                f"Confidence: {self.confidence:.4f}")


def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Compute cosine similarity between two embedding vectors.
    
    For normalized embeddings (unit length), this simplifies to the dot product:
    similarity = dot(emb1, emb2) / (||emb1|| × ||emb2||) = dot(emb1, emb2)
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
        
    Returns:
        Cosine similarity score in range [-1, 1], typically [0, 1] for normalized embeddings
    """
    # Ensure numpy arrays
    if isinstance(embedding1, list):
        embedding1 = np.array(embedding1)
    if isinstance(embedding2, list):
        embedding2 = np.array(embedding2)
    
    # Compute dot product
    dot_product = np.dot(embedding1, embedding2)
    
    # For normalized embeddings, this is sufficient
    # For unnormalized, would need: dot_product / (norm1 * norm2)
    return float(dot_product)


def verify_embeddings(
    embedding1: FaceEmbedding,
    embedding2: FaceEmbedding,
    threshold: float = 0.85
) -> FaceVerificationResult:
    """
    Verify if two face embeddings belong to the same person.
    
    This function compares two embeddings using cosine similarity and determines
    if they match based on a threshold.
    
    Privacy Note:
    - Only embeddings are compared, not raw images
    - The comparison reveals only whether faces match, not what they look like
    - No information about the original images is leaked
    
    Args:
        embedding1: First face embedding
        embedding2: Second face embedding
        threshold: Similarity threshold for match decision (default: 0.85, conservative)
        
    Returns:
        FaceVerificationResult containing match decision and similarity score
        
    Example:
        >>> emb1 = FaceEmbedding(vector=[...], model_name="facenet_v1", ...)
        >>> emb2 = FaceEmbedding(vector=[...], model_name="facenet_v1", ...)
        >>> result = verify_embeddings(emb1, emb2, threshold=0.85)
        >>> print(result.is_match)
        True
    """
    # Ensure embeddings are normalized
    if not embedding1.is_normalized():
        embedding1 = embedding1.normalize()
    if not embedding2.is_normalized():
        embedding2 = embedding2.normalize()
    
    # Compute cosine similarity
    similarity = cosine_similarity(embedding1.vector, embedding2.vector)
    
    # Make decision based on threshold
    is_match = similarity >= threshold
    
    # Compute confidence (distance from threshold)
    confidence = abs(similarity - threshold)
    
    # Use model name from embeddings (should be same, but handle mismatch)
    model_name = embedding1.model_name
    if embedding1.model_name != embedding2.model_name:
        model_name = f"{embedding1.model_name}/{embedding2.model_name}"
    
    return FaceVerificationResult(
        is_match=is_match,
        similarity_score=similarity,
        threshold_used=threshold,
        confidence=confidence,
        model_name=model_name
    )


def get_optimal_threshold(context: str = "general") -> float:
    """
    Get optimal similarity threshold for a given context.
    
    Different contexts may require different thresholds:
    - Registration: Stricter (0.90) - first-time verification, high security
    - Login: Moderate (0.85) - regular verification, balanced
    - Account Recovery: Stricter (0.90) - sensitive operation
    - Transaction: Moderate (0.85) - balance security and usability
    - Research/Testing: Conservative (0.85) - security-first approach
    
    Args:
        context: Context for threshold selection
        
    Returns:
        Optimal threshold value (0-1)
    """
    thresholds = {
        "registration": 0.90,
        "login": 0.85,
        "account_recovery": 0.90,
        "transaction": 0.85,
        "high_security": 0.90,
        "general": 0.85,
        "research": 0.85  # Conservative for research prototype
    }
    return thresholds.get(context, 0.85)


def batch_verify(
    reference_embedding: FaceEmbedding,
    candidate_embeddings: List[FaceEmbedding],
    threshold: float = 0.85
) -> List[FaceVerificationResult]:
    """
    Verify a reference embedding against multiple candidate embeddings.
    
    Useful for:
    - One-to-many verification (find matching face in database)
    - Batch verification operations
    - Identity search
    
    Args:
        reference_embedding: Reference face embedding
        candidate_embeddings: List of candidate embeddings to compare against
        threshold: Similarity threshold
        
    Returns:
        List of FaceVerificationResult objects
    """
    results = []
    for candidate in candidate_embeddings:
        result = verify_embeddings(reference_embedding, candidate, threshold)
        results.append(result)
    
    return results

