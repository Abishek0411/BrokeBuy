# 📐 Face Embedding Contract

## Interface Specification

This document defines the contract for face embeddings used in privacy-preserving face verification.

## FaceEmbedding Structure

### Definition

A **FaceEmbedding** is a fixed-size numerical vector (typically 512 or 128 dimensions) that represents the essential features of a face. It is extracted from a face image using a pre-trained neural network.

### Properties

1. **Fixed Size**: All embeddings have the same dimensionality (e.g., 512 floats)
2. **Normalized**: Embeddings are typically L2-normalized (unit length)
3. **Irreversible**: Cannot be reverse-engineered to reconstruct the original face
4. **Discriminative**: Different faces produce different embeddings
5. **Stable**: Same face under different conditions (lighting, angle) produces similar embeddings

### Data Structure

```python
from typing import List
from datetime import datetime

class FaceEmbedding:
    """
    Represents a face embedding extracted from a face image.
    
    Attributes:
        embedding_vector: List of floats (typically 512 dimensions)
        user_id: ID of the user this embedding belongs to
        extracted_at: Timestamp when embedding was extracted
        model_version: Version of the embedding model used
        image_hash: Hash of the original image (for audit, not reconstruction)
    """
    embedding_vector: List[float]  # e.g., [0.123, -0.456, ..., 0.789] (512 floats)
    user_id: str
    extracted_at: datetime
    model_version: str  # e.g., "facenet_v1", "arcface_v2"
    image_hash: str     # SHA-256 hash of original image
```

### Storage Format

Embeddings are stored as:
- **Database**: Array of floats in MongoDB
- **File**: JSON or binary format
- **Size**: ~2KB per embedding (512 floats × 4 bytes = 2048 bytes)

## Similarity Metrics

### Cosine Similarity (Primary)

**Formula:**
```
similarity = dot(embedding_1, embedding_2) / (||embedding_1|| × ||embedding_2||)
```

Since embeddings are normalized (unit length):
```
similarity = dot(embedding_1, embedding_2)
```

**Range**: [-1, 1] (typically [0, 1] for normalized embeddings)  
**Interpretation**:
- **1.0**: Identical faces (same person)
- **0.8-0.99**: Very similar (likely same person)
- **0.5-0.8**: Somewhat similar (possibly same person)
- **< 0.5**: Different faces (different people)

**Advantages**:
- Scale-invariant (works with normalized embeddings)
- Computationally efficient (dot product)
- Well-suited for high-dimensional vectors

### Euclidean Distance (Alternative)

**Formula:**
```
distance = ||embedding_1 - embedding_2||
```

**Range**: [0, ∞) (typically [0, 2] for normalized embeddings)  
**Interpretation**:
- **0**: Identical faces
- **< 0.5**: Very similar (likely same person)
- **0.5-1.0**: Somewhat similar
- **> 1.0**: Different faces

**Conversion to Similarity**:
```
similarity = 1 - (distance / 2)  # For normalized embeddings
```

### L2 Distance (Normalized)

**Formula:**
```
distance = ||embedding_1 - embedding_2||_2
similarity = 1 / (1 + distance)
```

**Range**: [0, 1]  
**Interpretation**: Similar to cosine similarity

## Threshold Concepts

### Verification Threshold

A **threshold** is a similarity score cutoff used to make verification decisions:

```python
def verify(embedding_1: FaceEmbedding, embedding_2: FaceEmbedding, threshold: float = 0.8) -> bool:
    similarity = cosine_similarity(embedding_1.embedding_vector, embedding_2.embedding_vector)
    return similarity >= threshold
```

### Threshold Selection

Threshold selection involves balancing:
- **Security**: Higher threshold = fewer false positives (more secure)
- **Usability**: Lower threshold = fewer false negatives (more user-friendly)

**Typical Thresholds**:
- **Strict (0.9)**: High security, may reject legitimate users
- **Balanced (0.8)**: Good balance of security and usability
- **Lenient (0.7)**: More user-friendly, may accept impostors

### Threshold Optimization

Optimal threshold is determined by:
1. **ROC Curve**: Plot True Positive Rate vs. False Positive Rate
2. **EER (Equal Error Rate)**: Threshold where false positive rate = false negative rate
3. **Business Requirements**: Security vs. usability trade-off

### Adaptive Thresholds

Different thresholds for different scenarios:
- **Registration**: Stricter threshold (0.85) - first-time verification
- **Login**: Moderate threshold (0.8) - regular verification
- **Account Recovery**: Stricter threshold (0.85) - sensitive operation
- **Transaction**: Moderate threshold (0.8) - balance security and usability

## Verification Decision

### Binary Decision

```python
def verify_faces(embedding_1: FaceEmbedding, embedding_2: FaceEmbedding) -> VerificationResult:
    similarity = cosine_similarity(embedding_1.embedding_vector, embedding_2.embedding_vector)
    threshold = get_threshold_for_context(context="login")
    
    is_match = similarity >= threshold
    
    return VerificationResult(
        is_match=is_match,
        similarity_score=similarity,
        threshold=threshold,
        confidence=abs(similarity - threshold)  # Higher confidence if far from threshold
    )
```

### Confidence Levels

- **High Confidence Match**: similarity > threshold + 0.1
- **Match**: similarity >= threshold
- **Uncertain**: threshold - 0.1 < similarity < threshold
- **No Match**: similarity < threshold - 0.1

## Privacy Guarantees

### What Embeddings Reveal

✅ **Can Determine**:
- If two embeddings are from the same person
- General facial characteristics (age range, gender, ethnicity) - if model is biased

❌ **Cannot Determine**:
- Exact appearance of the face
- Unique identifying features (moles, scars, etc.)
- Original image pixels

### Reverse Engineering Resistance

**Claim**: Face embeddings cannot be reverse-engineered to reconstruct the original face.

**Evidence**:
- Embeddings are high-dimensional (512D) but original images are much higher dimensional (e.g., 224×224×3 = 150,528D)
- Information loss during encoding (many-to-one mapping)
- No known successful reverse engineering attacks on modern face embedding models

**Privacy Level**: **High** - Embeddings provide strong privacy protection compared to raw images.

## Integration Contract

### Input

```python
# Single verification
embedding_1: FaceEmbedding = extract_embedding(face_image_1)
embedding_2: FaceEmbedding = extract_embedding(face_image_2)
result: bool = verify(embedding_1, embedding_2)
```

### Output

```python
class VerificationResult:
    is_match: bool              # True if faces match
    similarity_score: float     # Similarity score (0-1)
    threshold: float            # Threshold used
    confidence: float           # Confidence in the decision
    model_version: str          # Embedding model version
```

### Error Handling

- **Invalid Image**: Return error if face not detected in image
- **Low Quality**: Return error if image quality is too low
- **Multiple Faces**: Return error if multiple faces detected
- **Model Error**: Return error if embedding extraction fails

---

**Contract Version**: 1.0.0  
**Last Updated**: [Date]  
**Status**: Architecture Phase (Implementation Pending)

