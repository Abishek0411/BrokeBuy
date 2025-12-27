"""
DEMO ONLY – NOT FOR PRODUCTION

Demo API routes for project review demonstrations.

These routes are completely isolated from production code and only work
when DEMO_MODE=True is set in configuration.

IMPORTANT:
- No database writes
- No authentication required (demo only)
- All data is synthetic/mock
- Risk scores simulate GNN output but are NOT real ML predictions
"""

import random
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Literal
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from app.config import DEMO_MODE
from demo.fraud_simulation import compute_demo_risk_score, get_demo_risk_category
from demo.face_verification_demo import verify_demo_face

router = APIRouter(prefix="/demo", tags=["Demo"])


def _generate_synthetic_user(user_id: str, is_spam: bool = False) -> Dict[str, Any]:
    """
    DEMO ONLY – NOT FOR PRODUCTION
    
    Generates a synthetic user for demonstration purposes.
    
    Args:
        user_id: Unique identifier for the user
        is_spam: Whether this user should simulate spam behavior
        
    Returns:
        Synthetic user dictionary
    """
    return {
        "user_id": user_id,
        "name": f"Demo User {user_id[-4:]}",
        "email": f"demo{user_id[-4:]}@example.com",
        "is_spam": is_spam
    }


def _generate_synthetic_messages(
    user_id: str,
    message_count: int,
    is_spam: bool = False
) -> List[Dict[str, Any]]:
    """
    DEMO ONLY – NOT FOR PRODUCTION
    
    Generates synthetic messages for demonstration purposes.
    
    For spam users:
    - High message count
    - Very short response times (bot-like)
    
    For normal users:
    - Moderate message count
    - Normal response times
    
    Args:
        user_id: User identifier
        message_count: Number of messages to generate
        is_spam: Whether to simulate spam behavior
        
    Returns:
        List of synthetic message dictionaries
    """
    messages = []
    base_time = datetime.now(timezone.utc) - timedelta(days=7)
    
    if is_spam:
        # Spam: Very short intervals (1-5 seconds)
        interval_range = (1, 5)
    else:
        # Normal: Longer intervals (5 minutes to 2 hours)
        interval_range = (300, 7200)
    
    current_time = base_time
    for i in range(message_count):
        messages.append({
            "sender_id": user_id,
            "receiver_id": f"receiver_{random.randint(1, 10)}",
            "message": f"Demo message {i+1}",
            "timestamp": current_time
        })
        
        # Add random interval for next message
        interval = random.uniform(*interval_range)
        current_time = current_time + timedelta(seconds=interval)
    
    return messages


@router.post("/fraud-simulation")
async def demo_fraud_simulation() -> Dict[str, Any]:
    """
    DEMO ONLY – NOT FOR PRODUCTION
    
    Simulates fraud detection using demo risk scoring.
    
    This endpoint:
    - Generates synthetic users (mix of normal and spam)
    - Simulates message patterns
    - Computes demo risk scores (simulates GNN output)
    - Returns risk assessment results
    
    IMPORTANT:
    - Risk scores simulate GNN output but are NOT real ML predictions
    - All data is synthetic/mock
    - No database writes
    - No authentication required (demo only)
    - Results are for demonstration purposes only
    
    Returns:
        JSON response with users, risk scores, and graph structure:
        {
            "users": [
                {
                    "user_id": "...",
                    "messages_sent": 42,
                    "risk_score": 0.91,
                    "status": "FLAGGED",
                    "explanation": "..."
                }
            ],
            "graph": {
                "nodes": [
                    {
                        "id": "user_1",
                        "label": "Normal User",
                        "risk_score": 0.12,
                        "is_flagged": false
                    },
                    {
                        "id": "user_spammer",
                        "label": "Spammer",
                        "risk_score": 0.93,
                        "is_flagged": true
                    }
                ],
                "edges": [
                    {
                        "source": "user_spammer",
                        "target": "user_2",
                        "message_count": 12
                    }
                ]
            },
            "note": "DEMO ONLY - Risk scores simulate GNN output. Graph is illustrative, not real GNN internals."
        }
    """
    # Check DEMO_MODE
    if not DEMO_MODE:
        raise HTTPException(
            status_code=403,
            detail="DEMO ONLY: This endpoint requires DEMO_MODE=True. "
                   "This is not for production use."
        )
    
    # Generate synthetic users
    # Mix of normal users and spam users for demonstration
    synthetic_users = []
    
    # Normal users (low risk)
    for i in range(3):
        user_id = f"user_normal_{i+1}"
        user = _generate_synthetic_user(user_id, is_spam=False)
        synthetic_users.append(user)
    
    # Spam users (high risk)
    for i in range(3):
        user_id = f"user_spam_{i+1}"
        user = _generate_synthetic_user(user_id, is_spam=True)
        synthetic_users.append(user)
    
    # Compute risk scores for each user
    results = []
    user_risk_scores = {}  # Store risk scores for graph generation
    
    for user in synthetic_users:
        # Generate synthetic messages based on user type
        if user["is_spam"]:
            # Spam users: high message count (30-60 messages)
            message_count = random.randint(30, 60)
        else:
            # Normal users: moderate message count (5-15 messages)
            message_count = random.randint(5, 15)
        
        messages = _generate_synthetic_messages(
            user["user_id"],
            message_count,
            is_spam=user["is_spam"]
        )
        
        # Compute demo risk score (simulates GNN output)
        # NOTE: This is NOT real GNN inference, just simulation
        risk_score, explanation = compute_demo_risk_score(user, messages)
        user_risk_scores[user["user_id"]] = risk_score
        
        # Determine status based on risk score
        if risk_score >= 0.6:
            status = "FLAGGED"
        elif risk_score >= 0.3:
            status = "REVIEW"
        else:
            status = "CLEAR"
        
        results.append({
            "user_id": user["user_id"],
            "messages_sent": message_count,
            "risk_score": round(risk_score, 2),
            "status": status,
            "explanation": explanation
        })
    
    # Generate graph structure for visualization
    # Graph is illustrative, not real GNN internals
    # Nodes represent users, edges represent message interactions
    nodes = []
    edges = []
    
    for user in synthetic_users:
        risk_score = user_risk_scores[user["user_id"]]
        is_flagged = risk_score >= 0.6
        
        # Create user label
        if user["is_spam"]:
            label = f"Spammer ({user['user_id']})"
        else:
            label = f"Normal User ({user['user_id']})"
        
        nodes.append({
            "id": user["user_id"],
            "label": label,
            "risk_score": round(risk_score, 2),
            "is_flagged": is_flagged
        })
    
    # Generate edges representing message interactions
    # Spam users tend to message multiple normal users (spam pattern)
    # Normal users have fewer, more targeted interactions
    spam_users = [u["user_id"] for u in synthetic_users if u["is_spam"]]
    normal_users = [u["user_id"] for u in synthetic_users if not u["is_spam"]]
    
    # Spam users send messages to multiple normal users
    for spam_user in spam_users:
        # Each spam user messages 2-3 normal users
        targets = random.sample(normal_users, min(random.randint(2, 3), len(normal_users)))
        for target in targets:
            # High message count reflects spam intensity
            message_count = random.randint(10, 25)
            edges.append({
                "source": spam_user,
                "target": target,
                "message_count": message_count
            })
    
    # Normal users have fewer, more balanced interactions
    for normal_user in normal_users:
        # Each normal user might message 1-2 other users
        other_users = [u for u in synthetic_users if u["user_id"] != normal_user]
        if other_users:
            targets = random.sample([u["user_id"] for u in other_users], 
                                  min(random.randint(0, 2), len(other_users)))
            for target in targets:
                # Lower message count for normal interactions
                message_count = random.randint(2, 8)
                edges.append({
                    "source": normal_user,
                    "target": target,
                    "message_count": message_count
                })
    
    return {
        "users": results,
        "graph": {
            "nodes": nodes,
            "edges": edges
        },
        "note": "DEMO ONLY - Risk scores simulate GNN output but are NOT real ML predictions. "
                "This is for demonstration purposes only. Graph is illustrative, not real GNN internals."
    }


class FaceVerifyRequest(BaseModel):
    """Request model for face verification demo"""
    embedding_1: List[float]
    embedding_2: List[float]


@router.post("/face-verify")
async def demo_face_verify(request: FaceVerifyRequest) -> Dict[str, Any]:
    """
    DEMO ONLY – NOT FOR PRODUCTION
    
    Simulates face verification using fake embeddings received from client.
    
    This endpoint:
    - Accepts simulated embeddings from client (no real images used)
    - Computes cosine similarity between embeddings
    - Returns verification result based on similarity threshold
    
    IMPORTANT:
    - Received embeddings are simulated
    - No biometric data is processed or stored
    - No real images are used
    - No image storage
    - Results are for demonstration purposes only
    
    Args:
        request: FaceVerifyRequest with embedding_1 and embedding_2 arrays
        
    Returns:
        JSON response with similarity score and verification result:
        {
            "similarity": 0.82,
            "result": "MATCH",
            "note": "DEMO ONLY - Received embeddings are simulated, not real"
        }
    """
    # Check DEMO_MODE
    if not DEMO_MODE:
        raise HTTPException(
            status_code=403,
            detail="DEMO ONLY: This endpoint requires DEMO_MODE=True. "
                   "This is not for production use."
        )
    
    # Import cosine similarity function
    from demo.face_verification_demo import cosine_similarity
    import numpy as np
    
    # Convert embeddings to numpy arrays
    # Received embeddings are simulated. No biometric data is processed or stored.
    embedding1 = np.array(request.embedding_1, dtype=np.float32)
    embedding2 = np.array(request.embedding_2, dtype=np.float32)
    
    # Compute cosine similarity
    similarity = cosine_similarity(embedding1, embedding2)
    
    # Verification threshold (standard for face verification)
    threshold = 0.8
    
    # Determine result based on threshold
    if similarity >= threshold:
        result = "MATCH"
    else:
        result = "NO_MATCH"
    
    return {
        "similarity": round(similarity, 2),
        "result": result,
        "note": "DEMO ONLY - Received embeddings are simulated. No biometric data is processed or stored."
    }

