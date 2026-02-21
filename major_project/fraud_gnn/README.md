# 🔍 Graph-Based Fraud & Spam Detection using GNNs

## Problem Definition

Online marketplaces like BrokeBuy face significant challenges in detecting fraudulent activities and spam content. Traditional rule-based systems are limited by their inability to capture complex relational patterns between users, listings, messages, and devices. Fraudsters often exploit these limitations by creating sophisticated attack patterns that span multiple entities and interactions.

### Why Graph-Based Fraud Detection?

Fraud in marketplaces is inherently **relational**. Consider these scenarios:

1. **Sybil Attacks**: A fraudster creates multiple accounts (`UserNode`) that interact with each other to build fake credibility
2. **Collusion Networks**: Groups of users coordinate to manipulate listings, reviews, or transactions
3. **Device Fingerprinting**: Multiple accounts (`UserNode`) sharing the same device (`DeviceNode`) indicate potential fraud
4. **Message Patterns**: Suspicious communication patterns (`MessageEdge`) between users can reveal spam rings
5. **Listing Manipulation**: Coordinated listing creation, price manipulation, or fake transactions

Traditional rule-based systems fail because they:
- Only examine individual entities in isolation
- Cannot capture multi-hop relationships (e.g., "User A → Listing → User B → Device → User C")
- Require manual feature engineering that misses emerging patterns
- Are easily circumvented by adaptive attackers

### Graph Neural Networks (GNNs) Advantage

GNNs excel at learning from graph-structured data by:
- **Message Passing**: Aggregating information from neighboring nodes to learn node representations
- **Heterogeneous Graph Learning**: Handling multiple node types (users, listings, devices) and edge types (messages, transactions, device-sharing)
- **Pattern Discovery**: Automatically learning complex fraud patterns without explicit feature engineering
- **Scalability**: Processing large graphs efficiently through graph convolution operations

## Research Objectives

### Primary Objectives

1. **Graph Construction**: Design a heterogeneous graph representation of BrokeBuy marketplace data that captures all relevant fraud signals
2. **Feature Engineering**: Extract meaningful features from raw data that serve as node and edge attributes
3. **GNN Architecture**: Design and implement a Graph Neural Network architecture suitable for fraud detection
4. **Risk Scoring**: Develop a risk scoring mechanism that outputs interpretable risk scores (0-1) for users, listings, and transactions

### Secondary Objectives

1. **Real-time Detection**: Enable real-time fraud detection as new nodes and edges are added to the graph
2. **Explainability**: Provide explanations for why a particular entity received a high risk score
3. **Adaptive Learning**: Enable the model to adapt to new fraud patterns over time

## What Makes This Different from Rule-Based Systems

### Rule-Based Systems (Traditional Approach)

```
IF user.account_age < 7 days AND user.listings_count > 10:
    THEN flag as suspicious
```

**Limitations:**
- Static rules that don't adapt
- Cannot capture complex multi-entity relationships
- High false positive rates
- Easy to game once rules are known
- Requires constant manual updates

### Graph-Based GNN Approach (This Research)

```
Graph Structure → GNN Message Passing → Learned Representations → Risk Score
```

**Advantages:**
- Learns from graph structure automatically
- Captures multi-hop relationships (e.g., "User connected to 5 other users who all share the same device")
- Adapts to new patterns through training
- Lower false positive rates through context-aware decisions
- Harder to game due to holistic graph analysis

### Key Differentiators

1. **Relational Context**: Considers the entire network context, not just individual attributes
2. **Automatic Pattern Discovery**: Discovers fraud patterns that humans might miss
3. **Scalability**: Can process thousands of nodes and edges efficiently
4. **Transfer Learning**: Patterns learned from one marketplace can potentially transfer to others

## Research Questions

1. **Graph Structure**: What is the optimal heterogeneous graph structure for marketplace fraud detection?
2. **Feature Importance**: Which node and edge features are most predictive of fraud?
3. **GNN Architecture**: Which GNN variant (GCN, GraphSAGE, GAT, etc.) performs best for this task?
4. **Temporal Dynamics**: How do we handle evolving graphs as new transactions occur?
5. **Interpretability**: How can we explain GNN predictions to build trust with administrators?

## Evaluation Goals

- **Accuracy**: High precision and recall on fraud detection
- **False Positive Rate**: Minimize legitimate users flagged as fraudsters
- **Latency**: Real-time risk scoring (< 100ms per entity)
- **Scalability**: Handle graphs with 10,000+ nodes efficiently
- **Explainability**: Provide interpretable risk factors for flagged entities

## Integration with BrokeBuy

This module will serve as a **Trust & Safety engine** that:
- Analyzes the marketplace graph structure
- Generates risk scores for users, listings, and transactions
- Triggers appropriate actions (rate limiting, verification, blocking)
- Operates independently from core BrokeBuy business logic

See `risk_contract.md` for detailed integration specifications.

---

**Research Status**: Architecture & Skeleton Phase  
**Next Steps**: Graph construction, feature extraction, GNN model design

