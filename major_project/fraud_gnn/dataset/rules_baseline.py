"""
Rules-Based Baseline Detector

This module implements a baseline fraud detection system using only flat
features (counts, rates) without any graph awareness. This serves as a
fair baseline to compare against graph-based models.

Why This Is a Fair Baseline
----------------------------

1. **Standard Approach**: Rule-based systems are the industry standard for
   fraud detection. Most production systems use rules before moving to ML.

2. **Same Input Data**: The baseline uses the same user activity data that
   graph models use, just without the graph structure. This ensures fair
   comparison.

3. **Interpretable**: Rules are easy to understand and explain, making them
   suitable for production systems where explainability is required.

4. **No Graph Bias**: By not using graph structure, we can measure how much
   the graph structure actually helps. If graph models don't outperform
   this baseline, the graph structure might not be adding value.

5. **Realistic Comparison**: This represents what a system would do without
   graph-based detection, so it's a realistic baseline.

Why Graph-Based Models Should Outperform
-----------------------------------------

Graph-based models should outperform this baseline because:

1. **Relational Context**: Graph models can see that User A and User B share
   a device, or that User A is connected to many high-risk users. The baseline
   only sees individual user features.

2. **Pattern Discovery**: Graph models can discover complex fraud patterns
   (e.g., circular transactions, coordinated spam rings) that rules cannot
   capture.

3. **Network Effects**: Fraud often involves networks of accounts working
   together. Graph models can detect these networks; the baseline cannot.

4. **Feature Learning**: Graph models learn which graph patterns are
   predictive, while rules require manual feature engineering.

5. **Adaptability**: Graph models can adapt to new fraud patterns through
   training, while rules require manual updates.

Expected Performance Gap:
- Baseline: ~70-80% accuracy (good at obvious cases)
- Graph Model: ~85-95% accuracy (better at complex patterns)
"""

from typing import Dict
from datetime import datetime

from ..schema import GraphSnapshot, UserNode


def baseline_risk_score(user_activity: Dict) -> float:
    """
    Compute risk score for a user using only flat features (no graph).
    
    This baseline uses simple heuristics based on:
    - Account age
    - Activity rates (listings, messages)
    - Verification status
    - Activity patterns
    
    The score ranges from 0.0 (no risk) to 1.0 (high risk).
    
    Why These Features?
    --------------------
    
    1. **Account Age**: New accounts are riskier (fraudsters create new accounts)
    2. **Activity Rate**: Unusually high activity suggests automation or spam
    3. **Verification**: Verified accounts are generally more trustworthy
    4. **Activity Patterns**: Legitimate users have consistent patterns
    
    Limitations:
    ------------
    
    - Cannot detect Sybil attacks (no device sharing information)
    - Cannot detect collusion networks (no network structure)
    - Cannot detect coordinated spam (no message network analysis)
    - May have high false positive rate (legitimate new users flagged)
    - May miss sophisticated fraud (rules are simple)
    
    Args:
        user_activity: Dictionary containing user activity features:
            - account_age_days: int
            - listings_count: int
            - messages_sent: int
            - messages_received: int
            - transactions_count: int
            - verification_status: bool
            - avg_listing_price: float (optional)
            
    Returns:
        Risk score between 0.0 and 1.0
        
    Example:
        >>> activity = {
        ...     'account_age_days': 2,
        ...     'listings_count': 15,
        ...     'messages_sent': 50,
        ...     'verification_status': False
        ... }
        >>> risk = baseline_risk_score(activity)
        >>> print(f"Risk score: {risk:.2f}")
    """
    risk_score = 0.0
    
    # Feature 1: Account Age
    # New accounts (< 7 days) are riskier
    account_age = user_activity.get('account_age_days', 0)
    if account_age < 1:
        risk_score += 0.3  # Very new account
    elif account_age < 7:
        risk_score += 0.2  # New account
    elif account_age < 30:
        risk_score += 0.1  # Relatively new
    
    # Feature 2: Listing Activity Rate
    # High listing creation rate suggests spam
    listings_count = user_activity.get('listings_count', 0)
    if account_age > 0:
        listings_per_day = listings_count / account_age
    else:
        listings_per_day = listings_count  # Infinite rate for new accounts
    
    if listings_per_day > 10:
        risk_score += 0.3  # Very high rate
    elif listings_per_day > 5:
        risk_score += 0.2  # High rate
    elif listings_per_day > 2 and account_age < 7:
        risk_score += 0.15  # High for new account
    
    # Feature 3: Message Activity Rate
    # High message rate suggests spam or automation
    messages_sent = user_activity.get('messages_sent', 0)
    if account_age > 0:
        messages_per_day = messages_sent / account_age
    else:
        messages_per_day = messages_sent
    
    if messages_per_day > 50:
        risk_score += 0.25  # Very high rate
    elif messages_per_day > 20:
        risk_score += 0.15  # High rate
    elif messages_per_day > 10 and account_age < 7:
        risk_score += 0.1  # High for new account
    
    # Feature 4: Verification Status
    # Verified accounts are less risky
    is_verified = user_activity.get('verification_status', False)
    if is_verified:
        risk_score -= 0.2  # Reduce risk for verified accounts
        risk_score = max(0.0, risk_score)  # Don't go negative
    
    # Feature 5: Transaction Activity
    # Users with no transactions but many listings might be spam
    transactions_count = user_activity.get('transactions_count', 0)
    if listings_count > 5 and transactions_count == 0:
        risk_score += 0.15  # Suspicious: many listings, no sales
    
    # Feature 6: Activity Balance
    # Legitimate users typically have balanced activity (some listings,
    # some messages, some transactions). Extreme imbalance is suspicious.
    total_activity = listings_count + messages_sent + transactions_count
    if total_activity > 0:
        listing_ratio = listings_count / total_activity
        message_ratio = messages_sent / total_activity
        
        # Very high listing ratio (mostly listings, little interaction)
        if listing_ratio > 0.8:
            risk_score += 0.1
        # Very high message ratio (mostly messages, few listings)
        if message_ratio > 0.9:
            risk_score += 0.1
    
    # Normalize to [0, 1] range
    risk_score = min(1.0, risk_score)
    
    return risk_score


def compute_baseline_scores_for_snapshot(
    graph_snapshot: GraphSnapshot
) -> Dict[str, float]:
    """
    Compute baseline risk scores for all users in a snapshot.
    
    This extracts flat features from user nodes and computes risk scores
    without using any graph structure.
    
    Args:
        graph_snapshot: GraphSnapshot containing user nodes
        
    Returns:
        Dictionary mapping user_id -> risk_score (0-1)
    """
    scores = {}
    
    for user_id, user_node in graph_snapshot.user_nodes.items():
        # Extract flat features from user node
        user_activity = {
            'account_age_days': user_node.account_age_days,
            'listings_count': user_node.listings_count,
            'messages_sent': user_node.messages_sent,
            'messages_received': user_node.messages_received,
            'transactions_count': user_node.transactions_count,
            'verification_status': user_node.verification_status,
            'avg_listing_price': user_node.avg_listing_price
        }
        
        # Compute baseline risk score
        scores[user_id] = baseline_risk_score(user_activity)
    
    return scores


def compare_with_graph_model(
    baseline_scores: Dict[str, float],
    graph_scores: Dict[str, float],
    labels: Dict[str, int]
) -> Dict[str, float]:
    """
    Compare baseline and graph model performance.
    
    This is a utility function for evaluation (not implemented in detail
    as it requires ML evaluation metrics).
    
    Args:
        baseline_scores: Risk scores from baseline detector
        graph_scores: Risk scores from graph model
        labels: Ground truth labels (0=normal, 1=suspicious, 2=fraud)
        
    Returns:
        Dictionary with comparison metrics (to be implemented)
    """
    # TODO: Implement comparison metrics:
    # - Accuracy
    # - Precision/Recall
    # - F1-score
    # - ROC-AUC
    # - Confusion matrices
    
    return {
        'baseline_accuracy': 0.0,  # Placeholder
        'graph_accuracy': 0.0,      # Placeholder
        'improvement': 0.0          # Placeholder
    }

