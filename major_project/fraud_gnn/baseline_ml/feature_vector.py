"""
Feature Vector Construction for Baseline ML Models

This module constructs feature vectors for users using ONLY flat features
(no graph structure). These features are used to train traditional ML models
(Logistic Regression, Random Forest, Gradient Boosting) as baselines before
implementing graph neural networks.

Why No Graph Features?
-----------------------

This is intentional! We want to establish a fair baseline that:
1. Uses the same input data as graph models (user activity)
2. Does NOT use graph structure (no network information)
3. Represents what traditional ML can achieve without graph awareness

This allows us to measure the value added by graph structure. If graph models
don't significantly outperform these baselines, the graph structure might not
be adding value.

Why These Features?
-------------------

Each feature is chosen because it captures a signal that is predictive of
fraud, but without requiring graph structure:

1. **Account Age**: New accounts are riskier (fraudsters create new accounts)
2. **Activity Rates**: Unusually high rates suggest automation or spam
3. **Device Diversity**: Multiple devices might indicate account sharing or bots
4. **Reports**: User reports are strong fraud signals
5. **Text Similarity**: Copy-paste spam has high text similarity

These features can be computed from individual user data without knowing
about connections to other users.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import Counter
import re


def build_user_feature_vector(
    user: Dict,
    listings: List[Dict],
    messages: List[Dict],
    devices: Optional[List[Dict]] = None
) -> Dict[str, float]:
    """
    Build a feature vector for a user using only flat features (no graph).
    
    This function extracts features from a user's individual activity without
    considering their connections to other users or the graph structure.
    
    Features Extracted:
    -------------------
    
    1. **account_age_days**: Age of the account in days
       - Why: New accounts are riskier (fraudsters create new accounts)
       - Range: 0 to thousands of days
       
    2. **messages_sent_per_hour**: Average messages sent per hour
       - Why: High message rates suggest spam bots or automation
       - Range: 0 to potentially very high
       
    3. **listings_posted_per_hour**: Average listings created per hour
       - Why: Burst listing creation suggests spam or fake inventory
       - Range: 0 to potentially very high
       
    4. **unique_devices_used**: Number of unique devices associated with user
       - Why: Multiple devices might indicate account sharing or bot networks
       - Range: 1 to potentially many
       
    5. **reports_received**: Number of reports/complaints received
       - Why: User reports are strong fraud indicators
       - Range: 0 to potentially many
       
    6. **avg_message_similarity**: Average similarity between user's messages
       - Why: Copy-paste spam has high similarity (repetitive content)
       - Range: 0.0 to 1.0
       
    7. **avg_listing_similarity**: Average similarity between user's listings
       - Why: Spam listings often have similar titles/descriptions
       - Range: 0.0 to 1.0
       
    Why This Ignores Graph Structure Intentionally:
    -----------------------------------------------
    
    - We want to measure what traditional ML can achieve WITHOUT graph awareness
    - Graph models will use these same features PLUS graph structure
    - This creates a fair baseline for comparison
    - If graph models don't outperform, graph structure might not be valuable
    
    Args:
        user: User dictionary with fields like:
            - user_id, created_at, messages_sent, listings_count, etc.
        listings: List of listing dictionaries created by this user
            Each dict should have: listing_id, title, description, created_at, etc.
        messages: List of message dictionaries sent by this user
            Each dict should have: message_id, content, created_at, etc.
        devices: Optional list of device dictionaries associated with user
            Each dict should have: device_id, etc.
            
    Returns:
        Dictionary mapping feature names to float values
        
    Example:
        >>> user = {'user_id': 'u1', 'created_at': '2024-01-01', ...}
        >>> listings = [{'title': 'Item 1', ...}, ...]
        >>> messages = [{'content': 'Hello', ...}, ...]
        >>> features = build_user_feature_vector(user, listings, messages)
        >>> print(features['account_age_days'])
        30.0
    """
    features = {}
    
    # Feature 1: Account Age
    user_created = _parse_datetime(user.get('created_at'))
    if user_created:
        account_age = (datetime.utcnow() - user_created).total_seconds() / 86400  # days
    else:
        account_age = 0.0
    features['account_age_days'] = account_age
    
    # Feature 2: Messages Sent Per Hour
    messages_sent = user.get('messages_sent', 0)
    if account_age > 0:
        # Convert days to hours
        account_age_hours = account_age * 24
        messages_per_hour = messages_sent / account_age_hours if account_age_hours > 0 else 0.0
    else:
        # New account: use messages from messages list if available
        if messages:
            # Estimate based on messages in the list
            message_times = [_parse_datetime(m.get('created_at')) for m in messages]
            message_times = [t for t in message_times if t is not None]
            if message_times:
                time_span = (max(message_times) - min(message_times)).total_seconds() / 3600
                messages_per_hour = len(messages) / time_span if time_span > 0 else len(messages)
            else:
                messages_per_hour = len(messages)
        else:
            messages_per_hour = 0.0
    features['messages_sent_per_hour'] = messages_per_hour
    
    # Feature 3: Listings Posted Per Hour
    listings_count = user.get('listings_count', len(listings))
    if account_age > 0:
        account_age_hours = account_age * 24
        listings_per_hour = listings_count / account_age_hours if account_age_hours > 0 else 0.0
    else:
        # New account: use listings from listings list if available
        if listings:
            listing_times = [_parse_datetime(l.get('created_at')) for l in listings]
            listing_times = [t for t in listing_times if t is not None]
            if listing_times:
                time_span = (max(listing_times) - min(listing_times)).total_seconds() / 3600
                listings_per_hour = len(listings) / time_span if time_span > 0 else len(listings)
            else:
                listings_per_hour = len(listings)
        else:
            listings_per_hour = 0.0
    features['listings_posted_per_hour'] = listings_per_hour
    
    # Feature 4: Unique Devices Used
    if devices:
        unique_devices = len(set(d.get('device_id') for d in devices if d.get('device_id')))
    else:
        # Try to get from user data
        unique_devices = user.get('unique_devices_count', 1)  # Default to 1 if unknown
    features['unique_devices_used'] = float(unique_devices)
    
    # Feature 5: Reports Received
    reports_received = user.get('reports_received', 0)
    features['reports_received'] = float(reports_received)
    
    # Feature 6: Average Message Similarity
    if messages and len(messages) > 1:
        message_contents = [m.get('content', '') for m in messages if m.get('content')]
        if message_contents:
            avg_similarity = _compute_avg_text_similarity(message_contents)
        else:
            avg_similarity = 0.0
    else:
        avg_similarity = 0.0
    features['avg_message_similarity'] = avg_similarity
    
    # Feature 7: Average Listing Similarity
    if listings and len(listings) > 1:
        listing_texts = []
        for listing in listings:
            # Combine title and description
            title = listing.get('title', '')
            description = listing.get('description', '')
            listing_texts.append(f"{title} {description}".strip())
        if listing_texts:
            avg_similarity = _compute_avg_text_similarity(listing_texts)
        else:
            avg_similarity = 0.0
    else:
        avg_similarity = 0.0
    features['avg_listing_similarity'] = avg_similarity
    
    # Additional features that might be useful
    features['listings_count'] = float(listings_count)
    features['messages_sent'] = float(messages_sent)
    features['transactions_count'] = float(user.get('transactions_count', 0))
    features['verification_status'] = 1.0 if user.get('verification_status', False) else 0.0
    features['avg_listing_price'] = float(user.get('avg_listing_price', 0.0))
    
    return features


def _parse_datetime(value) -> Optional[datetime]:
    """Parse datetime from various formats."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except:
            try:
                return datetime.fromtimestamp(float(value))
            except:
                return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value)
    return None


def _compute_avg_text_similarity(texts: List[str]) -> float:
    """
    Compute average pairwise similarity between texts.
    
    Uses Jaccard similarity on word sets (simple but effective for spam detection).
    
    Why Jaccard Similarity?
    - Fast to compute
    - Good for detecting copy-paste spam (high similarity)
    - Doesn't require word order (good for spam variations)
    
    Args:
        texts: List of text strings
        
    Returns:
        Average pairwise Jaccard similarity (0.0 to 1.0)
    """
    if len(texts) < 2:
        return 0.0
    
    def jaccard_similarity(text1: str, text2: str) -> float:
        """Compute Jaccard similarity between two texts."""
        # Tokenize into words (simple whitespace split)
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 and not words2:
            return 1.0  # Both empty
        if not words1 or not words2:
            return 0.0  # One empty
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    # Compute pairwise similarities
    similarities = []
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            sim = jaccard_similarity(texts[i], texts[j])
            similarities.append(sim)
    
    return sum(similarities) / len(similarities) if similarities else 0.0


def build_feature_matrix(
    users: List[Dict],
    user_listings: Dict[str, List[Dict]],
    user_messages: Dict[str, List[Dict]],
    user_devices: Optional[Dict[str, List[Dict]]] = None
) -> tuple:
    """
    Build feature matrix for all users.
    
    This is a convenience function that builds feature vectors for multiple users
    and returns them as a matrix (list of feature dicts) and user IDs.
    
    Args:
        users: List of user dictionaries
        user_listings: Dictionary mapping user_id -> list of listings
        user_messages: Dictionary mapping user_id -> list of messages
        user_devices: Optional dictionary mapping user_id -> list of devices
        
    Returns:
        Tuple of (feature_matrix, user_ids) where:
        - feature_matrix: List of feature dictionaries
        - user_ids: List of user IDs in same order
    """
    feature_matrix = []
    user_ids = []
    
    if user_devices is None:
        user_devices = {}
    
    for user in users:
        user_id = str(user.get('user_id', user.get('_id', '')))
        listings = user_listings.get(user_id, [])
        messages = user_messages.get(user_id, [])
        devices = user_devices.get(user_id, [])
        
        features = build_user_feature_vector(user, listings, messages, devices)
        feature_matrix.append(features)
        user_ids.append(user_id)
    
    return feature_matrix, user_ids

