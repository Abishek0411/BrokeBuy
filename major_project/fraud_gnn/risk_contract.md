# 🎯 Risk Scoring Contract

## Interface Specification

This document defines the clean interface between the fraud detection GNN model and the BrokeBuy platform.

## Input Contract

### Input: GraphSnapshot

The model accepts a `GraphSnapshot` object (defined in `schema.py`) containing:
- **User nodes**: All users in the marketplace
- **Listing nodes**: All active listings
- **Device nodes**: Device fingerprints
- **Edges**: Messages, transactions, creates, device associations, views

The graph snapshot represents the state of the marketplace at a specific point in time.

### Input Format

```python
from fraud_gnn.schema import GraphSnapshot

# GraphSnapshot is built from BrokeBuy database data
graph_snapshot: GraphSnapshot = build_graph_from_brokebuy_data(...)
```

## Output Contract

### Output: RiskScore

The model outputs risk scores in the range **[0.0, 1.0]** where:
- **0.0**: No risk detected (legitimate entity)
- **1.0**: Maximum risk (highly suspicious/fraudulent)

### Risk Score Types

The model can generate risk scores for different entity types:

1. **User Risk Score**: Risk associated with a user account
2. **Listing Risk Score**: Risk associated with a listing
3. **Transaction Risk Score**: Risk associated with a transaction
4. **Device Risk Score**: Risk associated with a device fingerprint

### Output Format

```python
# For a single entity
risk_score: float = compute_risk_score(graph_snapshot, entity_id, entity_type)
# Returns: 0.0 <= risk_score <= 1.0

# For multiple entities (batch processing)
risk_scores: Dict[str, float] = compute_risk_scores_batch(graph_snapshot, entity_ids, entity_type)
# Returns: {"entity_id_1": 0.23, "entity_id_2": 0.87, ...}
```

## Risk Score Interpretation

### Thresholds (Configurable)

- **Low Risk (0.0 - 0.3)**: Normal operation, no action needed
- **Medium Risk (0.3 - 0.6)**: Monitor closely, apply light restrictions
- **High Risk (0.6 - 0.8)**: Apply restrictions, require verification
- **Critical Risk (0.8 - 1.0)**: Block immediately, flag for review

### Risk Factors

The risk score aggregates multiple signals:
- Account age and activity patterns
- Network structure (connections to other risky entities)
- Behavioral anomalies (unusual patterns)
- Device sharing (Sybil detection)
- Message patterns (spam detection)
- Economic patterns (price manipulation, etc.)

## Integration with BrokeBuy

### How BrokeBuy Consumes Risk Scores

The fraud detection module operates as an **external Trust & Safety engine**. BrokeBuy calls the risk scoring function and uses the results to make decisions.

#### 1. Rate Limiting

```python
# Example: Apply rate limits based on risk score
user_risk = get_user_risk_score(user_id)

if user_risk > 0.6:
    # High-risk user: stricter rate limits
    max_listings_per_day = 2
    max_messages_per_hour = 5
elif user_risk > 0.3:
    # Medium-risk user: moderate rate limits
    max_listings_per_day = 5
    max_messages_per_hour = 20
else:
    # Low-risk user: normal limits
    max_listings_per_day = 10
    max_messages_per_hour = 50
```

#### 2. Verification Triggers

```python
# Example: Require additional verification for high-risk users
if user_risk > 0.7:
    trigger_verification_flow(user_id)
    # Could include: phone verification, ID verification, face verification
```

#### 3. Listing Moderation

```python
# Example: Flag suspicious listings for review
listing_risk = get_listing_risk_score(listing_id)

if listing_risk > 0.8:
    # Critical risk: hide listing immediately
    hide_listing(listing_id)
    flag_for_admin_review(listing_id)
elif listing_risk > 0.5:
    # High risk: require manual approval
    require_listing_approval(listing_id)
```

#### 4. Transaction Blocking

```python
# Example: Block transactions involving high-risk entities
buyer_risk = get_user_risk_score(buyer_id)
seller_risk = get_user_risk_score(seller_id)
listing_risk = get_listing_risk_score(listing_id)

if max(buyer_risk, seller_risk, listing_risk) > 0.8:
    block_transaction(transaction_id, reason="High risk score")
```

#### 5. Real-time Monitoring

```python
# Example: Monitor new entities in real-time
def on_new_user_registered(user_id):
    graph_snapshot = get_current_graph_snapshot()
    risk_score = compute_risk_score(graph_snapshot, user_id, NodeType.USER)
    
    if risk_score > 0.6:
        log_suspicious_activity(user_id, risk_score)
        notify_admins(user_id, risk_score)
```

## API Boundary (Future)

While no API endpoints are implemented yet, the future interface will be:

```
POST /major-project/fraud-gnn/risk-score
{
    "entity_id": "user_123",
    "entity_type": "user"
}

Response:
{
    "risk_score": 0.73,
    "risk_level": "high",
    "factors": ["new_account", "device_sharing", "suspicious_network"],
    "timestamp": "2024-01-15T10:30:00Z"
}
```

## Performance Requirements

- **Latency**: Risk score computation should complete in < 100ms for single entities
- **Throughput**: Support batch processing of 100+ entities per second
- **Scalability**: Handle graphs with 10,000+ nodes efficiently

## Error Handling

- If graph snapshot is invalid: Return error, don't compute risk score
- If entity not found: Return `None` or raise `EntityNotFoundError`
- If model not loaded: Return default risk score (0.5) or raise `ModelNotReadyError`

## Versioning

Risk score computation may evolve over time. The contract should support:
- Model versioning (different GNN architectures)
- Feature versioning (different feature sets)
- Threshold versioning (different risk thresholds)

---

**Contract Version**: 1.0.0  
**Last Updated**: [Date]  
**Status**: Architecture Phase (Implementation Pending)

