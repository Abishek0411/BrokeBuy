"""
Rule-Based Labeling Strategy

This module implements rule-based labeling for users in graph snapshots.
Labels are used as ground truth (or weak supervision) for training and
evaluating fraud detection models.

Why Rule-Based Labeling?
------------------------

In real-world fraud detection systems, we rarely have perfect ground truth.
Fraud is often discovered after the fact, and many fraudsters are never caught.
Rule-based labeling provides:

1. **Scalability**: Can label thousands of users automatically
2. **Consistency**: Same rules applied to all users
3. **Explainability**: We know exactly why a user was labeled as fraud
4. **Weak Supervision**: Even imperfect labels can train good models

Why Perfect Labels Are Impossible
----------------------------------

1. **Unknown Fraud**: Many fraudsters are never caught or reported
2. **False Positives**: Legitimate users might exhibit suspicious patterns
3. **Context Missing**: Rules can't capture all context (e.g., legitimate
   reasons for high activity)
4. **Evolving Patterns**: Fraud patterns change, so rules become outdated
5. **Human Error**: Even manual labeling by experts has errors

Why Weak Supervision Is Acceptable
-----------------------------------

Weak supervision (imperfect labels) is acceptable for research because:

1. **Model Learning**: GNNs can learn patterns beyond the rules used for labeling
2. **Feature Learning**: Even with noisy labels, models learn useful features
3. **Comparative Evaluation**: We can compare models on the same (imperfect) labels
4. **Real-World Relevance**: Real systems also have imperfect ground truth
5. **Research Focus**: The goal is to show GNNs outperform baselines, not
   achieve perfect accuracy

The labeling rules approximate ground truth by capturing known fraud patterns:
- Burst activity (spam accounts)
- Device sharing (Sybil attacks)
- Text similarity (copy-paste spam)
- Suspicious networks (collusion)

These patterns are strong indicators of fraud, even if not 100% accurate.
"""

from typing import Dict, List, Set
from collections import defaultdict
from datetime import datetime, timedelta
import re

from ..schema import GraphSnapshot, UserNode, MessageEdge


def label_users(graph_snapshot: GraphSnapshot) -> Dict[str, int]:
    """
    Label users in a graph snapshot using rule-based heuristics.
    
    Labels:
    - 0: Normal (legitimate user)
    - 1: Suspicious (exhibits some fraud indicators)
    - 2: Spam/Fraud (exhibits multiple strong fraud indicators)
    
    Labeling Rules:
    --------------
    
    1. **Message Burst Rate**: Users sending many messages in short time
       → Indicator of spam bots or automated accounts
       
    2. **Listing Burst Rate**: Users creating many listings quickly
       → Indicator of spam listings or fake inventory
       
    3. **Text Similarity**: Similar text across listings/messages
       → Indicator of copy-paste spam or automated content
       
    4. **Device Sharing**: Multiple users sharing same device
       → Strong indicator of Sybil attack (same person, multiple accounts)
       
    5. **Account Age vs Activity**: New accounts with high activity
       → Suspicious (legitimate users typically build activity gradually)
       
    6. **Isolated Accounts**: Accounts with no connections
       → Might be spam (legitimate users typically interact)
       
    7. **Suspicious Network**: Accounts connected to many high-risk accounts
       → Guilt by association
    
    Args:
        graph_snapshot: GraphSnapshot to label users in
        
    Returns:
        Dictionary mapping user_id -> label (0, 1, or 2)
        
    Example:
        >>> labels = label_users(snapshot)
        >>> print(f"Labeled {len(labels)} users")
        >>> print(f"Fraud: {sum(1 for l in labels.values() if l == 2)}")
    """
    labels = {}
    
    # Initialize all users as normal (0)
    for user_id in graph_snapshot.user_nodes:
        labels[user_id] = 0
    
    # Compute fraud indicators for each user
    fraud_scores = _compute_fraud_scores(graph_snapshot)
    
    # Label based on fraud scores
    for user_id, score in fraud_scores.items():
        if score >= 3.0:  # Multiple strong indicators
            labels[user_id] = 2  # Spam/Fraud
        elif score >= 1.5:  # Some indicators
            labels[user_id] = 1  # Suspicious
        else:
            labels[user_id] = 0  # Normal
    
    return labels


def _compute_fraud_scores(graph_snapshot: GraphSnapshot) -> Dict[str, float]:
    """
    Compute fraud scores for each user based on multiple indicators.
    
    Returns a dictionary mapping user_id -> fraud_score (0-5+).
    Higher scores indicate more fraud indicators.
    """
    scores = defaultdict(float)
    
    # Indicator 1: Message burst rate
    message_burst_scores = _compute_message_burst_scores(graph_snapshot)
    for user_id, score in message_burst_scores.items():
        scores[user_id] += score
    
    # Indicator 2: Listing burst rate
    listing_burst_scores = _compute_listing_burst_scores(graph_snapshot)
    for user_id, score in listing_burst_scores.items():
        scores[user_id] += score
    
    # Indicator 3: Device sharing
    device_sharing_scores = _compute_device_sharing_scores(graph_snapshot)
    for user_id, score in device_sharing_scores.items():
        scores[user_id] += score
    
    # Indicator 4: Account age vs activity
    age_activity_scores = _compute_age_activity_scores(graph_snapshot)
    for user_id, score in age_activity_scores.items():
        scores[user_id] += score
    
    # Indicator 5: Network isolation
    isolation_scores = _compute_isolation_scores(graph_snapshot)
    for user_id, score in isolation_scores.items():
        scores[user_id] += score
    
    # Indicator 6: Suspicious network (guilt by association)
    network_scores = _compute_network_scores(graph_snapshot, scores)
    for user_id, score in network_scores.items():
        scores[user_id] += score * 0.5  # Weighted less (indirect indicator)
    
    return dict(scores)


def _compute_message_burst_scores(graph_snapshot: GraphSnapshot) -> Dict[str, float]:
    """
    Detect users with high message burst rates (spam indicator).
    
    Fraudsters often send many messages in short time windows.
    """
    scores = {}
    
    for user_id, user_node in graph_snapshot.user_nodes.items():
        # Count messages sent by this user
        messages_sent = sum(
            edge.message_count
            for edge in graph_snapshot.message_edges
            if edge.from_user_id == user_id
        )
        
        # Compute messages per day
        if user_node.account_age_days > 0:
            messages_per_day = messages_sent / user_node.account_age_days
        else:
            messages_per_day = messages_sent  # New account, very suspicious
        
        # High message rate is suspicious
        # Threshold: >10 messages/day for new accounts, >50/day for any account
        if user_node.account_age_days < 7 and messages_per_day > 10:
            scores[user_id] = 1.5  # Strong indicator for new accounts
        elif messages_per_day > 50:
            scores[user_id] = 1.0  # Moderate indicator
        else:
            scores[user_id] = 0.0
    
    return scores


def _compute_listing_burst_scores(graph_snapshot: GraphSnapshot) -> Dict[str, float]:
    """
    Detect users with high listing creation rates (spam indicator).
    
    Fraudsters often create many listings quickly to flood the marketplace.
    """
    scores = {}
    
    # Group listings by seller and creation time
    listings_by_seller = defaultdict(list)
    for listing in graph_snapshot.listing_nodes.values():
        listings_by_seller[listing.seller_id].append(listing.created_at)
    
    for user_id, user_node in graph_snapshot.user_nodes.items():
        if user_id not in listings_by_seller:
            continue
        
        listing_times = sorted(listings_by_seller[user_id])
        listing_count = len(listing_times)
        
        # Compute listings per day
        if user_node.account_age_days > 0:
            listings_per_day = listing_count / user_node.account_age_days
        else:
            listings_per_day = listing_count
        
        # Check for burst pattern (many listings in short time)
        if listing_count >= 2:
            time_span = (max(listing_times) - min(listing_times)).total_seconds()
            if time_span > 0:
                listings_per_hour = listing_count / (time_span / 3600)
            else:
                listings_per_hour = float('inf')  # All at once, very suspicious
        else:
            listings_per_hour = 0
        
        # High listing rate is suspicious
        if listings_per_hour > 5:  # More than 5 listings per hour
            scores[user_id] = 2.0  # Very strong indicator
        elif listings_per_day > 10 and user_node.account_age_days < 7:
            scores[user_id] = 1.5  # Strong indicator for new accounts
        elif listings_per_day > 20:
            scores[user_id] = 1.0  # Moderate indicator
        else:
            scores[user_id] = 0.0
    
    return scores


def _compute_device_sharing_scores(graph_snapshot: GraphSnapshot) -> Dict[str, float]:
    """
    Detect users sharing devices (Sybil attack indicator).
    
    Multiple accounts from the same device strongly suggests Sybil attack.
    """
    scores = {}
    
    # Count users per device
    device_user_counts = {}
    for device in graph_snapshot.device_nodes.values():
        device_user_counts[device.device_id] = device.user_count
    
    # Score users based on device sharing
    for user_id, user_node in graph_snapshot.user_nodes.items():
        # Find devices used by this user
        user_devices = [
            device_id
            for device_id, device in graph_snapshot.device_nodes.items()
            if user_id in device.user_ids
        ]
        
        max_shared_users = 0
        for device_id in user_devices:
            shared_count = device_user_counts.get(device_id, 0)
            max_shared_users = max(max_shared_users, shared_count)
        
        # High device sharing is very suspicious
        if max_shared_users >= 5:  # 5+ users on same device
            scores[user_id] = 2.5  # Very strong Sybil indicator
        elif max_shared_users >= 3:  # 3-4 users
            scores[user_id] = 1.5  # Strong indicator
        elif max_shared_users >= 2:  # 2 users (could be legitimate)
            scores[user_id] = 0.5  # Weak indicator
        else:
            scores[user_id] = 0.0
    
    return scores


def _compute_age_activity_scores(graph_snapshot: GraphSnapshot) -> Dict[str, float]:
    """
    Detect new accounts with unusually high activity (suspicious).
    
    Legitimate users typically build activity gradually. Fraudsters often
    create accounts and immediately start spamming.
    """
    scores = {}
    
    for user_id, user_node in graph_snapshot.user_nodes.items():
        # New account (less than 7 days old)
        is_new_account = user_node.account_age_days < 7
        
        # High activity indicators
        high_listings = user_node.listings_count > 5
        high_messages = user_node.messages_sent > 20
        
        if is_new_account and (high_listings or high_messages):
            # Very suspicious: new account with high activity
            if high_listings and high_messages:
                scores[user_id] = 2.0  # Very strong indicator
            else:
                scores[user_id] = 1.0  # Moderate indicator
        else:
            scores[user_id] = 0.0
    
    return scores


def _compute_isolation_scores(graph_snapshot: GraphSnapshot) -> Dict[str, float]:
    """
    Detect isolated accounts (no connections).
    
    Legitimate users typically interact with others. Isolated accounts
    might be spam or fake accounts.
    """
    scores = {}
    
    for user_id, user_node in graph_snapshot.user_nodes.items():
        # Count connections (messages, transactions, etc.)
        message_connections = sum(
            1 for edge in graph_snapshot.message_edges
            if edge.from_user_id == user_id or edge.to_user_id == user_id
        )
        
        listing_connections = sum(
            1 for listing in graph_snapshot.listing_nodes.values()
            if listing.seller_id == user_id
        )
        
        total_connections = message_connections + listing_connections
        
        # Isolated account with activity is suspicious
        if total_connections == 0 and (user_node.listings_count > 0 or user_node.messages_sent > 0):
            scores[user_id] = 0.5  # Weak indicator (could be new user)
        else:
            scores[user_id] = 0.0
    
    return scores


def _compute_network_scores(
    graph_snapshot: GraphSnapshot,
    existing_scores: Dict[str, float]
) -> Dict[str, float]:
    """
    Compute guilt-by-association scores.
    
    Users connected to many high-risk users are themselves more risky.
    """
    scores = {}
    
    for user_id in graph_snapshot.user_nodes:
        # Find neighbors (users this user interacts with)
        neighbors = set()
        
        # Message neighbors
        for edge in graph_snapshot.message_edges:
            if edge.from_user_id == user_id:
                neighbors.add(edge.to_user_id)
            elif edge.to_user_id == user_id:
                neighbors.add(edge.from_user_id)
        
        # Compute average risk of neighbors
        neighbor_risks = [
            existing_scores.get(neighbor_id, 0.0)
            for neighbor_id in neighbors
        ]
        
        if neighbor_risks:
            avg_neighbor_risk = sum(neighbor_risks) / len(neighbor_risks)
            # If neighbors are high-risk, this user is also risky
            scores[user_id] = avg_neighbor_risk
        else:
            scores[user_id] = 0.0
    
    return scores


def _compute_text_similarity_scores(graph_snapshot: GraphSnapshot) -> Dict[str, float]:
    """
    Detect text similarity across listings/messages (copy-paste spam).
    
    Note: This is a stub. Full implementation would require:
    - Extracting text from listings/messages
    - Computing similarity (e.g., Jaccard, cosine similarity)
    - Detecting duplicate or near-duplicate content
    
    This is left as a stub because it requires access to listing descriptions
    and message content, which may not be available in the snapshot.
    """
    # TODO: Implement text similarity detection
    # This would involve:
    # 1. Extracting text from listings (title, description)
    # 2. Extracting text from messages
    # 3. Computing similarity between texts (Jaccard, TF-IDF, etc.)
    # 4. Flagging users with high text similarity across their content
    return {}

