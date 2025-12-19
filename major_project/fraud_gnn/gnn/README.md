# 🕸️ Graph Neural Network for Fraud Detection

## Overview

This module implements Graph Neural Networks (GNNs) using PyTorch Geometric for fraud and spam detection. GNNs leverage the graph structure of the marketplace to detect coordinated fraud patterns that traditional ML cannot capture.

## GNN Architecture

### Model: FraudGNN

**Architecture**:
```
Input Features (n_nodes, n_features)
    ↓
GraphSAGE/GAT Layers (message passing)
    ↓
Dropout (regularization)
    ↓
ReLU (non-linearity)
    ↓
Output: User-level fraud probability (n_users, n_classes)
```

**Components**:
- **Input Layer**: Node features (account age, activity rates, etc.)
- **GraphSAGE/GAT Layers**: Message passing to aggregate neighbor information
- **Dropout**: Prevents overfitting (default: 0.5)
- **ReLU**: Non-linear activation
- **Classifier**: Final layer for 3-class classification (normal, suspicious, fraud)

### Why GraphSAGE?

- **Scalability**: Can handle large graphs efficiently through neighbor sampling
- **Inductive Learning**: Can generalize to new nodes not seen during training
- **Flexible**: Works with different graph structures

### Why GAT (Graph Attention)?

- **Attention Mechanism**: Learns which neighbors are most important
- **Interpretability**: Attention weights show which connections matter
- **Better Performance**: Often outperforms GraphSAGE on fraud detection

## Training Setup

### Data Preparation

1. **Graph Snapshot**: Load from Step 2 dataset exports
2. **Feature Extraction**: Extract node features (users, listings, devices)
3. **Label Mapping**: Map user IDs to labels (0=normal, 1=suspicious, 2=fraud)
4. **Train/Val/Test Split**: 70/15/15 split on labeled users

### Training Configuration

- **Optimizer**: Adam
- **Learning Rate**: 0.01 (default)
- **Weight Decay**: 5e-4 (L2 regularization)
- **Loss Function**: CrossEntropyLoss with class weights
- **Early Stopping**: Patience=10 epochs
- **Batch Size**: Full graph (no batching for small graphs)

### Class Imbalance Handling

- **Class Weights**: Automatically computed (inverse frequency)
- **Stratified Splits**: Maintains class distribution in train/val/test
- **Focus on Recall**: Prioritizes catching fraud over precision

### Regularization

- **Dropout**: 0.5 (randomly zero 50% of features)
- **Weight Decay**: L2 regularization on model parameters
- **Early Stopping**: Prevents overfitting

## Expected Improvements Over Baselines

### Performance Gains

Compared to baseline ML models (Step 3):

- **Precision**: +5-10% improvement
- **Recall**: +10-15% improvement (critical for fraud detection)
- **F1-Score**: +8-12% improvement
- **ROC-AUC**: +0.05-0.10 improvement

### Why GNNs Outperform

1. **Network Structure**: Can see connections between users (device sharing, messages, transactions)
2. **Pattern Discovery**: Automatically discovers complex fraud patterns (Sybil attacks, collusion networks)
3. **Relational Context**: Understands that "User A shares device with User B" is different from independent users
4. **Feature Learning**: Learns graph-based features automatically (no manual engineering)

### Specific Fraud Types

GNNs are particularly good at detecting:

- **Sybil Attacks**: Multiple accounts sharing devices
- **Collusion Networks**: Coordinated fraud groups
- **Circular Transactions**: Fake transaction patterns
- **Guilt by Association**: Users connected to fraudsters

## Computational Tradeoffs

### Advantages

- **Automatic Feature Learning**: No manual graph feature engineering
- **Scalable**: Can handle graphs with 10,000+ nodes
- **Efficient**: Message passing is parallelizable

### Disadvantages

- **Training Time**: Slower than baseline ML (minutes vs seconds)
- **Memory**: Requires more memory for large graphs
- **Hyperparameter Tuning**: More hyperparameters to tune (layers, hidden dim, dropout)
- **Overfitting Risk**: Prone to overfitting on small datasets

### Computational Requirements

- **GPU**: Recommended for training (10x speedup)
- **Memory**: ~2-4GB for graphs with 10,000 nodes
- **Training Time**: 5-30 minutes depending on graph size and epochs

## Usage Example

```python
from fraud_gnn.gnn import (
    load_graph_snapshot,
    FraudGNN,
    train_model,
    evaluate_gnn,
    compare_with_baseline
)
from fraud_gnn.dataset import GraphSnapshotBuilder

# Load graph snapshot
snapshot = GraphSnapshotBuilder().build_snapshot(...)
labels = label_users(snapshot)

# Convert to PyTorch Geometric format
data = load_graph_snapshot(snapshot, labels)

# Create model
model = FraudGNN(
    input_dim=data.x.size(1),
    hidden_dim=64,
    output_dim=3,
    num_layers=2,
    dropout=0.5
)

# Train
results = train_model(
    model=model,
    data=data,
    epochs=100,
    lr=0.01,
    patience=10,
    checkpoint_dir='checkpoints/'
)

# Evaluate
gnn_results = evaluate_gnn(results['model'], data)

# Compare with baseline
baseline_results = {...}  # From Step 3
compare_with_baseline(gnn_results, baseline_results)
```

## Hyperparameter Tuning

### Key Hyperparameters

1. **Hidden Dimension**: 32, 64, 128 (larger = more capacity, risk of overfitting)
2. **Number of Layers**: 2, 3, 4 (deeper = more context, risk of overfitting)
3. **Dropout**: 0.3, 0.5, 0.7 (higher = more regularization)
4. **Learning Rate**: 0.001, 0.01, 0.1 (lower = slower but more stable)
5. **Weight Decay**: 1e-5, 5e-4, 1e-3 (higher = more regularization)

### Tuning Strategy

1. Start with default values
2. Tune learning rate first (most important)
3. Tune hidden dimension and layers
4. Tune dropout and weight decay
5. Use validation set to select best hyperparameters

## Model Variants

### FraudGNN (GraphSAGE)

- Uses GraphSAGE convolution
- Faster training
- Good baseline GNN

### FraudGNNWithAttention (GAT)

- Uses Graph Attention Network
- Attention weights show important neighbors
- Often better performance
- More interpretable

## Evaluation Metrics

Same metrics as baseline ML (Step 3):

- **Precision**: Of predicted fraud, how many are actually fraud?
- **Recall**: Of actual fraud, how many did we catch? (CRITICAL)
- **F1-Score**: Harmonic mean of precision and recall
- **ROC-AUC**: Model's ability to distinguish classes
- **Confusion Matrix**: Per-class performance

## Limitations

1. **Small Datasets**: Prone to overfitting on small graphs (< 1000 nodes)
2. **Computational Cost**: Slower than baseline ML
3. **Hyperparameter Sensitivity**: Performance depends on hyperparameters
4. **Graph Quality**: Requires good graph structure (connections matter)

## Future Enhancements

- [ ] Heterogeneous GNN (explicit handling of node/edge types)
- [ ] Temporal GNN (handle graph evolution over time)
- [ ] Graph sampling for large graphs
- [ ] Attention visualization (which neighbors matter?)
- [ ] Transfer learning (pre-train on large graph, fine-tune on small)

---

**Status**: GNN Implementation Complete  
**Framework**: PyTorch Geometric  
**Purpose**: Detect coordinated fraud through graph structure

