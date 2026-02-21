# 🔬 Research Questions & Hypotheses

## Overview

This document clearly states the research questions, hypotheses, and evaluation goals for the Major Project. The research focuses on two main areas:
1. Graph-based Fraud & Spam Detection using GNNs
2. Privacy-Preserving Face Verification using embeddings and federated learning

## Research Questions

### Fraud Detection Module (GNN)

#### RQ1: Graph Structure Effectiveness
**Question**: What is the optimal heterogeneous graph structure for marketplace fraud detection?

**Sub-questions**:
- Which node types (users, listings, devices) are most important for fraud detection?
- Which edge types (messages, transactions, device associations) capture the most fraud signals?
- How does graph density affect fraud detection accuracy?
- What is the optimal time window for graph snapshots?

**Hypothesis**: A heterogeneous graph with users, listings, and devices, connected through messages, transactions, and device associations, will outperform homogeneous graphs and rule-based systems.

**Evaluation**: Compare fraud detection accuracy across different graph structures using precision, recall, and F1-score.

---

#### RQ2: Feature Importance
**Question**: Which node and edge features are most predictive of fraudulent behavior?

**Sub-questions**:
- Are temporal features (account age, activity patterns) more important than network features?
- Do device-sharing features improve Sybil attack detection?
- Which message pattern features best detect spam?
- How do economic features (pricing patterns) contribute to fraud detection?

**Hypothesis**: Network features (device sharing, suspicious neighbor ratios) combined with temporal features (account age, activity rates) will be most predictive, with device features being critical for Sybil detection.

**Evaluation**: Feature importance analysis using SHAP values, ablation studies, and correlation analysis.

---

#### RQ3: GNN Architecture Selection
**Question**: Which Graph Neural Network variant performs best for marketplace fraud detection?

**Sub-questions**:
- How do GCN, GraphSAGE, and GAT compare for this task?
- Does attention mechanism (GAT) improve fraud detection?
- How does graph sampling (GraphSAGE) affect performance and scalability?
- Can heterogeneous GNNs (HeteroGNN) better handle multiple node/edge types?

**Hypothesis**: GraphSAGE with attention mechanism will perform best, balancing accuracy and scalability for large graphs.

**Evaluation**: Compare GNN architectures on the same dataset using accuracy, precision, recall, F1-score, and inference latency.

---

#### RQ4: Temporal Dynamics
**Question**: How do we effectively handle evolving graphs as new transactions and users are added?

**Sub-questions**:
- Should we retrain the model periodically or use incremental learning?
- How do we handle new nodes (cold start problem)?
- What is the optimal update frequency for graph snapshots?
- Can we use temporal GNNs to capture temporal patterns?

**Hypothesis**: Incremental graph updates with periodic model retraining will maintain accuracy while enabling real-time fraud detection.

**Evaluation**: Measure accuracy degradation over time, retraining frequency requirements, and real-time inference latency.

---

#### RQ5: Explainability
**Question**: How can we explain GNN predictions to build trust with administrators?

**Sub-questions**:
- Which graph sub-structures contribute most to high risk scores?
- Can we identify the most influential neighbors for a given node?
- How do we visualize graph-based explanations?
- Are explanations consistent and interpretable by humans?

**Hypothesis**: Subgraph-based explanations highlighting suspicious neighborhoods and device-sharing patterns will be most interpretable.

**Evaluation**: User studies with administrators, explanation consistency metrics, and explanation quality scores.

---

### Face Privacy Module

#### RQ6: Embedding-Based Verification Accuracy
**Question**: How does embedding-based face verification accuracy compare to raw image comparison?

**Sub-questions**:
- What is the verification accuracy (true positive rate, false positive rate)?
- How do different embedding models (FaceNet, ArcFace, etc.) compare?
- What is the optimal similarity threshold for verification?
- How does accuracy vary across different demographics?

**Hypothesis**: Embedding-based verification will achieve >99% true positive rate and <0.1% false positive rate, comparable to raw image comparison.

**Evaluation**: ROC curves, EER (Equal Error Rate), accuracy metrics on test dataset.

---

#### RQ7: Privacy Guarantees
**Question**: Can face embeddings be reverse-engineered to reconstruct original faces?

**Sub-questions**:
- What information can be extracted from embeddings (demographics, identity)?
- Are embeddings truly irreversible?
- What are the privacy risks compared to raw images?
- Can embeddings be used for cross-platform tracking?

**Hypothesis**: Face embeddings cannot be reverse-engineered to reconstruct original faces, providing strong privacy protection compared to raw images.

**Evaluation**: Reverse engineering attacks, information leakage analysis, privacy metrics.

---

#### RQ8: Similarity Metrics
**Question**: Which similarity metric (cosine, Euclidean, etc.) provides the best verification accuracy?

**Sub-questions**:
- How does cosine similarity compare to Euclidean distance?
- Are there better metrics for face embeddings?
- How do metrics perform with normalized vs. unnormalized embeddings?
- What is the optimal threshold for each metric?

**Hypothesis**: Cosine similarity will perform best for normalized embeddings, providing the highest accuracy.

**Evaluation**: Compare metrics on same dataset, measure accuracy and threshold sensitivity.

---

#### RQ9: Federated Learning Effectiveness
**Question**: Can federated learning achieve comparable accuracy to centralized training for face recognition?

**Sub-questions**:
- How many federated learning rounds are needed for convergence?
- How does federated learning handle non-IID data (different users have different face distributions)?
- What is the communication cost of federated learning?
- Can federated learning maintain privacy while achieving good accuracy?

**Hypothesis**: Federated learning will achieve comparable accuracy to centralized training (within 2-3%) while preserving privacy.

**Evaluation**: Compare federated vs. centralized training accuracy, measure communication costs, evaluate privacy guarantees.

---

#### RQ10: Threshold Optimization
**Question**: What similarity threshold provides optimal balance between security and usability?

**Sub-questions**:
- How do different thresholds affect false positive and false negative rates?
- Should thresholds be adaptive based on context (registration vs. login)?
- How do thresholds vary across different embedding models?
- What is the user experience impact of different thresholds?

**Hypothesis**: A threshold of 0.8 will provide optimal balance, with context-specific thresholds (0.85 for registration, 0.8 for login) improving user experience.

**Evaluation**: ROC curves, user studies, false positive/negative rate analysis.

---

## Hypotheses Summary

### Primary Hypotheses

1. **Graph-based fraud detection will outperform rule-based systems** in detecting complex fraud patterns, especially Sybil attacks and collusion networks.

2. **Heterogeneous graphs with device nodes will significantly improve Sybil detection** compared to user-listing only graphs.

3. **Face embeddings provide strong privacy protection** while maintaining verification accuracy comparable to raw image comparison.

4. **Federated learning can achieve comparable accuracy** to centralized training while preserving user privacy.

### Secondary Hypotheses

1. **Network features (device sharing, suspicious neighbors) will be more predictive** than individual entity features.

2. **GraphSAGE with attention will outperform other GNN architectures** for fraud detection in marketplaces.

3. **Cosine similarity will be optimal** for normalized face embeddings.

4. **Context-specific thresholds will improve user experience** without compromising security.

---

## Evaluation Goals

### Fraud Detection Module

- **Accuracy**: >95% precision, >90% recall on fraud detection
- **False Positive Rate**: <5% (legitimate users flagged as fraudsters)
- **Latency**: <100ms for single entity risk scoring
- **Scalability**: Handle graphs with 10,000+ nodes efficiently
- **Explainability**: Provide interpretable explanations for 80%+ of high-risk predictions

### Face Privacy Module

- **Verification Accuracy**: >99% true positive rate, <0.1% false positive rate
- **Privacy**: Demonstrate that embeddings cannot be reverse-engineered
- **Latency**: <200ms for embedding extraction, <10ms for verification
- **Storage**: 2KB per embedding (vs. 100KB+ for raw images)
- **Usability**: >95% verification success rate for legitimate users

### Overall Research Goals

- **Novelty**: Demonstrate new approaches to fraud detection and privacy-preserving verification
- **Practical Impact**: Show real-world applicability through BrokeBuy integration
- **Reproducibility**: Provide clear documentation and code for reproducibility
- **Scalability**: Demonstrate solutions that scale to production environments

---

## Research Methodology

### Data Collection
- Use BrokeBuy marketplace data (users, listings, messages, transactions)
- Synthetic fraud data generation for training (if needed)
- Public face recognition datasets for face verification evaluation

### Experimental Design
- Controlled experiments comparing different approaches
- Ablation studies to understand component contributions
- User studies for explainability and usability evaluation

### Evaluation Metrics
- Standard ML metrics (accuracy, precision, recall, F1-score)
- Privacy metrics (information leakage, reverse engineering resistance)
- Performance metrics (latency, throughput, scalability)
- Usability metrics (user satisfaction, verification success rate)

---

**Last Updated**: [Date]  
**Status**: Research Design Phase

