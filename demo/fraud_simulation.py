"""
DEMO ONLY – NOT FOR PRODUCTION

Demo fraud risk scoring simulation.

This module provides SIMULATED risk scoring for demonstration purposes only.
It does NOT use real GNN inference or machine learning models.

Purpose:
- Explain research output visually during project reviews
- Demonstrate how risk scoring works conceptually
- NOT to claim accuracy or real fraud detection

IMPORTANT:
- This is NOT real GNN inference
- This is NOT real ML model prediction
- This is a simple heuristic-based simulation
- Results are for demonstration only
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
from app.config import DEMO_MODE


def compute_demo_risk_score(
    user: Dict[str, Any],
    messages: List[Dict[str, Any]]
) -> Tuple[float, str]:
    """
    DEMO ONLY – NOT FOR PRODUCTION
    
    Simulates GNN-based risk scoring using simple heuristics.
    
    This function SIMULATES what a real GNN model would output, but uses
    simple rule-based heuristics instead of actual machine learning.
    
    Logic:
    - High message count → higher risk (potential spam/abuse)
    - Short response times → higher risk (bot-like behavior)
    
    Args:
        user: User dictionary with user information
        messages: List of message dictionaries with 'timestamp' field
        
    Returns:
        Tuple of (risk_score, explanation):
        - risk_score: Float between 0.0 (no risk) and 1.0 (maximum risk)
        - explanation: Human-readable string explaining the risk factors
        
    IMPORTANT:
    - This is NOT real GNN inference
    - This is NOT real ML model prediction
    - Results are for demonstration purposes only
    """
    if not DEMO_MODE:
        raise RuntimeError(
            "DEMO ONLY: This function requires DEMO_MODE=True. "
            "This is not for production use."
        )
    
    # Validate inputs
    if not messages:
        return 0.0, "No messages found - insufficient data for risk assessment"
    
    # Extract message timestamps
    message_times = []
    for msg in messages:
        timestamp = msg.get('timestamp')
        if timestamp:
            # Handle both datetime objects and ISO strings
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    continue
            elif isinstance(timestamp, datetime):
                pass
            else:
                continue
            
            message_times.append(timestamp)
    
    if len(message_times) < 2:
        return 0.0, "Insufficient message history for risk assessment (need at least 2 messages)"
    
    # Calculate message count
    message_count = len(message_times)
    
    # Calculate average response time (time between consecutive messages)
    sorted_times = sorted(message_times)
    response_intervals = []
    for i in range(1, len(sorted_times)):
        interval_seconds = (sorted_times[i] - sorted_times[i-1]).total_seconds()
        response_intervals.append(interval_seconds)
    
    avg_response_time_seconds = sum(response_intervals) / len(response_intervals) if response_intervals else 0.0
    
    # SIMULATED RISK SCORING (NOT REAL GNN INFERENCE)
    # These are simple heuristics that simulate GNN output for demonstration
    
    # Factor 1: Message count risk
    # High message count suggests potential spam or coordinated activity
    # Threshold: >50 messages = high risk, >20 = medium risk
    if message_count > 50:
        message_count_risk = 0.6
    elif message_count > 20:
        message_count_risk = 0.3
    elif message_count > 10:
        message_count_risk = 0.15
    else:
        message_count_risk = 0.05
    
    # Factor 2: Response time risk
    # Very short response times (< 5 seconds) suggest bot-like behavior
    # Very long response times (> 1 hour) are normal
    if avg_response_time_seconds < 5:
        response_time_risk = 0.5  # Very suspicious - bot-like
    elif avg_response_time_seconds < 30:
        response_time_risk = 0.3  # Suspicious - automated responses
    elif avg_response_time_seconds < 300:  # 5 minutes
        response_time_risk = 0.15  # Slightly suspicious
    else:
        response_time_risk = 0.05  # Normal human response time
    
    # Combine factors (weighted average)
    # Message count is more important for detecting spam rings
    combined_risk = (message_count_risk * 0.6) + (response_time_risk * 0.4)
    
    # Cap at 1.0
    risk_score = min(combined_risk, 1.0)
    
    # Generate explanation
    explanation_parts = []
    
    if message_count > 50:
        explanation_parts.append(f"Very high message count ({message_count} messages)")
    elif message_count > 20:
        explanation_parts.append(f"High message count ({message_count} messages)")
    elif message_count > 10:
        explanation_parts.append(f"Moderate message count ({message_count} messages)")
    else:
        explanation_parts.append(f"Normal message count ({message_count} messages)")
    
    if avg_response_time_seconds < 5:
        explanation_parts.append(f"extremely fast response time ({avg_response_time_seconds:.1f}s avg) - bot-like behavior")
    elif avg_response_time_seconds < 30:
        explanation_parts.append(f"very fast response time ({avg_response_time_seconds:.1f}s avg) - potentially automated")
    elif avg_response_time_seconds < 300:
        explanation_parts.append(f"fast response time ({avg_response_time_seconds:.1f}s avg)")
    else:
        explanation_parts.append(f"normal response time ({avg_response_time_seconds:.1f}s avg)")
    
    explanation = f"Simulated risk assessment: {'; '.join(explanation_parts)}. "
    explanation += f"Combined risk score: {risk_score:.2f} (0.0 = no risk, 1.0 = maximum risk). "
    explanation += "NOTE: This is a DEMO simulation, not real GNN inference."
    
    return risk_score, explanation


def get_demo_risk_category(risk_score: float) -> str:
    """
    DEMO ONLY – NOT FOR PRODUCTION
    
    Categorizes risk score into human-readable categories.
    
    Args:
        risk_score: Risk score between 0.0 and 1.0
        
    Returns:
        Risk category string
    """
    if not DEMO_MODE:
        raise RuntimeError(
            "DEMO ONLY: This function requires DEMO_MODE=True. "
            "This is not for production use."
        )
    
    if risk_score >= 0.8:
        return "CRITICAL RISK"
    elif risk_score >= 0.6:
        return "HIGH RISK"
    elif risk_score >= 0.3:
        return "MEDIUM RISK"
    elif risk_score >= 0.1:
        return "LOW RISK"
    else:
        return "NO RISK"

